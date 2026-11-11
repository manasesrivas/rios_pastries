from rest_framework import serializers

from detail_orders.models import DetailOrder

from .models import Order
from .utils import is_store_open


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


def validate_unique_products(items):
    product_ids = [item['product_id'] for item in items]
    if len(product_ids) != len(set(product_ids)):
        raise serializers.ValidationError({
            'items': 'No repitas productos; indica la cantidad total en un solo elemento.'
        })


class OrderItemsInputSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate_items(self, items):
        validate_unique_products(items)
        return items


class OrderDetailSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = DetailOrder
        fields = (
            'id',
            'product_id',
            'product_name',
            'quantity',
            'price',
            'subtotal',
            'status',
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemInputSerializer(many=True, write_only=True, allow_empty=False)
    details = OrderDetailSerializer(source='order', many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'subtotal',
            'total',
            'fecha',
            'hora',
            'direccion',
            'metodo_pago',
            'tipo_entrega',
            'status',
            'items',
            'details',
        )
        read_only_fields = (
            'id',
            'user',
            'subtotal',
            'total',
            'fecha',
            'hora',
            'status',
        )

    def validate(self, attrs):
        validate_unique_products(attrs['items'])
        if not is_store_open():
            raise serializers.ValidationError(
                'El horario para realizar pedidos en línea es de 9:00 a. m. a 7:00 p. m.'
            )
        return attrs
