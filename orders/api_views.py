from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .order_service import (
    IdempotencyKeyConflict,
    UnavailableProductsError,
    create_order,
    validate_products_availability,
)
from .serializers import OrderItemsInputSerializer, OrderSerializer


class OrderModelPermissions(DjangoModelPermissions):
    perms_map = {
        **DjangoModelPermissions.perms_map,
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
    }


class OrderListCreateAPIView(ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [OrderModelPermissions]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related(
            'user',
        ).prefetch_related(
            'order__product',
            'order__status',
        ).order_by('-fecha', '-hora', '-pk')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try: 
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    'message': 'El horario para realizar pedidos en línea es de 9:00 a. m. a 7:00 p. m.'
                },
                status=status.HTTP_409_CONFLICT
            )
        idempotency_key = request.headers.get('Idempotency-Key', '').strip()
        if len(idempotency_key) > 255:
            raise ValidationError({
                'Idempotency-Key': 'La clave no puede superar 255 caracteres.'
            })

        order_data = {
            key: value
            for key, value in serializer.validated_data.items()
            if key != 'items'
        }
        try:
            result = create_order(
                user=request.user,
                order_data=order_data,
                items=serializer.validated_data['items'],
                idempotency_key=idempotency_key or None,
            )
        except ValidationError as e:
            return Response(
                {
                    'message': 'error xd',
                    'errors': 'errors'
                },
                status=status.HTTP_400_CONFLICT,
            )
        except UnavailableProductsError as error:
            return Response(
                {
                    'code': 'CART_UNAVAILABLE_PRODUCTS',
                    'message': (
                        'No se puede completar el pedido porque existen '
                        'productos no disponibles.'
                    ),
                    'errors': error.errors,
                },
                status=status.HTTP_409_CONFLICT,
            )
        except IdempotencyKeyConflict:
            return Response(
                {
                    'code': 'IDEMPOTENCY_KEY_REUSED',
                    'message': (
                        'La clave de idempotencia ya se utilizó con otra solicitud.'
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        response_serializer = self.get_serializer(result.order)
        response_status = (
            status.HTTP_201_CREATED
            if result.created
            else status.HTTP_200_OK
        )
        return Response(response_serializer.data, status=response_status)


class ValidateCartAPIView(APIView):
    queryset = Order.objects.all()
    permission_classes = [OrderModelPermissions]

    def post(self, request):
        serializer = OrderItemsInputSerializer(data=request.data)
        try: 
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    'message': 'El horario para realizar pedidos en línea es de 9:00 a. m. a 7:00 p. m.'
                },
                status=status.HTTP_409_CONFLICT
            )

        _, errors = validate_products_availability(
            serializer.validated_data['items'],
        )
        if errors:
            return Response(
                {
                    'code': 'CART_UNAVAILABLE_PRODUCTS',
                    'message': (
                        'No se puede completar el pedido porque existen '
                        'productos no disponibles.'
                    ),
                    'errors': errors,
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response({'valid': True, 'code': 'CART_VALID'}, status=status.HTTP_200_OK)
