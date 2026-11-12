from django.utils import timezone

from rest_framework import serializers

from .models import EstadoReservacion, Reservation


class ReservationSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(read_only=True)
    estado = serializers.CharField(read_only=True)
    hallName = serializers.CharField(source='sala.name', read_only=True)
    venueName = serializers.CharField(source='sala.venue.name', read_only=True)
    venueAdress = serializers.CharField(
        source='sala.venue.address',
        read_only=True,
    )
    hall = serializers.SerializerMethodField()
    venue = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = (
            'id',
            'cliente',
            'fecha_evento',
            'cantidad_personas',
            'sala',
            'estado',
            'hallName',
            'venueName',
            'venueAdress',
            'hall',
            'venue',
        )

    def get_hall(self, obj):
        return None

    def get_venue(self, obj):
        return None

    def validate(self, attrs):
        fecha_evento = attrs.get('fecha_evento')
        sala = attrs.get('sala')
        cantidad_personas = attrs.get('cantidad_personas')

        if fecha_evento < timezone.localdate():
            raise serializers.ValidationError({
                'fecha_evento': 'No puedes elegir una fecha pasada.',
            })

        if cantidad_personas > sala.capacity:
            raise serializers.ValidationError({
                'cantidad_personas': (
                    f'La sala "{sala.name}" tiene capacidad para '
                    f'{sala.capacity} personas.'
                ),
            })

        sala_ocupada = Reservation.objects.filter(
            sala=sala,
            fecha_evento=fecha_evento,
        ).exclude(estado__in=[
            EstadoReservacion.CANCELADA,
            EstadoReservacion.ELIMINADA,
        ]).exists()
        if sala_ocupada:
            raise serializers.ValidationError({
                'fecha_evento': (
                    'Esta sala ya tiene una reservación activa para esa fecha.'
                ),
            })

        return attrs
