from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import serializers
from rest_framework.fields import get_error_detail

from halls.models import Hall
from products.models import Product
from products_reservations.models import ReservationItem

from .models import EstadoReservacion, INACTIVE_RESERVATION_STATES, Reservation


OCCUPIED_MESSAGE = 'Esta sala ya tiene una reservación activa para esa fecha.'
def active_reservations(sala, fecha_evento):
    return Reservation.objects.filter(
        sala=sala,
        fecha_evento=fecha_evento,
    ).exclude(estado__in=INACTIVE_RESERVATION_STATES)


def reservation_errors(attrs, instance=None):
    fecha_evento = attrs.get('fecha_evento', getattr(instance, 'fecha_evento', None))
    sala = attrs.get('sala', getattr(instance, 'sala', None))
    cantidad = attrs.get('cantidad_personas', getattr(instance, 'cantidad_personas', None))
    errors = {}

    if fecha_evento is not None and fecha_evento < timezone.localdate():
        errors['fecha_evento'] = ['No puedes elegir una fecha pasada.']

    if sala is not None and cantidad is not None and cantidad > sala.capacity:
        errors['cantidad_personas'] = [
            f'La sala "{sala.name}" tiene capacidad para {sala.capacity} personas.'
        ]

    if sala is not None and fecha_evento is not None:
        reservations = active_reservations(sala, fecha_evento)
        if instance is not None and instance.pk is not None:
            reservations = reservations.exclude(pk=instance.pk)
        if reservations.exists():
            errors.setdefault('fecha_evento', []).append(OCCUPIED_MESSAGE)
    return errors


class ReservationItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class ReservationItemSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(source='product_id', read_only=True)
    name = serializers.CharField(source='product.name', read_only=True)
    quantity = serializers.IntegerField(source='cantidad', read_only=True)
    price = serializers.DecimalField(
        source='precio_unitario', max_digits=10, decimal_places=2, read_only=True,
    )
    subtotal = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = ReservationItem
        fields = ('product', 'name', 'quantity', 'price', 'subtotal')


class ReservationSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(read_only=True)
    estado = serializers.CharField(read_only=True)
    hallName = serializers.CharField(source='sala.name', read_only=True)
    venueName = serializers.CharField(source='sala.venue.name', read_only=True)
    venueAdress = serializers.CharField(source='sala.venue.address', read_only=True)
    hall = serializers.SerializerMethodField()
    venue = serializers.SerializerMethodField()
    total_productos = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    items = ReservationItemSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = (
            'id', 'cliente', 'fecha_evento', 'cantidad_personas', 'sala', 'estado',
            'hallName', 'venueName', 'venueAdress', 'hall', 'venue',
            'total_productos', 'items',
        )
        validators = []

    def get_hall(self, obj):
        return None

    def get_venue(self, obj):
        return None

    def validate(self, attrs):
        errors = reservation_errors(attrs, self.instance)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ReservationValidationError(serializers.ValidationError):
    def __init__(self, detail):
        self.detail = detail


class ReservationCreateSerializer(ReservationSerializer):
    items = ReservationItemInputSerializer(many=True)

    def get_fields(self):
        fields = super().get_fields()
        require_items = getattr(settings, 'RESERVATIONS_REQUIRE_PRODUCTS', False)
        fields['items'].required = require_items
        fields['items'].allow_empty = not require_items
        return fields

    def validate_items(self, items):
        quantities = {}
        for item in items:
            product_id = item['product_id']
            quantities[product_id] = quantities.get(product_id, 0) + item['quantity']

        products = Product.objects.filter(pk__in=quantities)
        self.products_by_id = {product.pk: product for product in products}
        self.product_errors = []
        for product_id in quantities:
            product = self.products_by_id.get(product_id)
            if product is None:
                self.product_errors.append({
                    'product_id': product_id,
                    'name': None,
                    'error': 'El producto no existe o fue eliminado.',
                })
            elif not product.available:
                self.product_errors.append({
                    'product_id': product_id,
                    'name': product.name,
                    'error': f'El producto "{product.name}" no está disponible actualmente.',
                })
        return [
            {'product_id': product_id, 'quantity': quantity}
            for product_id, quantity in quantities.items()
        ]

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            return super().to_internal_value(data)

        attrs = {}
        errors = {}
        for field in self._writable_fields:
            validator = getattr(self, f'validate_{field.field_name}', None)
            try:
                value = field.run_validation(field.get_value(data))
                if validator is not None:
                    value = validator(value)
            except serializers.ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except serializers.SkipField:
                pass
            else:
                self.set_value(attrs, field.source_attrs, value)

        for field, messages in reservation_errors(attrs, self.instance).items():
            if field not in errors:
                errors[field] = messages
        if getattr(self, 'product_errors', None):
            errors['items'] = self.product_errors
        if errors:
            raise ReservationValidationError(errors)
        return attrs

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        items = validated_data.pop('items', [])
        sala = validated_data['sala']
        fecha_evento = validated_data['fecha_evento']
        try:
            with transaction.atomic():
                sala = Hall.objects.select_for_update().filter(pk=sala.pk).first()
                if sala is None:
                    raise serializers.ValidationError({'sala': ['La sala no existe.']})
                if validated_data['cantidad_personas'] > sala.capacity:
                    raise serializers.ValidationError({
                        'cantidad_personas': [
                            f'La sala "{sala.name}" tiene capacidad para {sala.capacity} personas.'
                        ],
                    })
                if active_reservations(sala, fecha_evento).exists():
                    raise serializers.ValidationError({'fecha_evento': [OCCUPIED_MESSAGE]})
                validated_data['sala'] = sala
                reservation = Reservation.objects.create(
                    **validated_data,
                    cliente=self.context['request'].user,
                    estado=EstadoReservacion.CONFIRMADA,
                )
                ReservationItem.objects.bulk_create([
                    ReservationItem(
                        reservation=reservation,
                        product=self.products_by_id[item['product_id']],
                        cantidad=item['quantity'],
                        precio_unitario=self.products_by_id[item['product_id']].price,
                    )
                    for item in items
                ])
        except IntegrityError:
            if active_reservations(sala, fecha_evento).exists():
                raise serializers.ValidationError({'fecha_evento': [OCCUPIED_MESSAGE]})
            raise
        return reservation
