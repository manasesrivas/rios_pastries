import hashlib
import json
from dataclasses import dataclass

from django.db import IntegrityError, transaction

from categories.models import Category
from detail_orders.models import DetailOrder, Status
from products.models import Product, StatusProduct

from .models import Order
from .services import publish_order_update


PRODUCT_NOT_FOUND = 'PRODUCT_NOT_FOUND'
PRODUCT_INACTIVE = 'PRODUCT_INACTIVE'


class UnavailableProductsError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('The order contains unavailable products.')


class IdempotencyKeyConflict(Exception):
    pass


@dataclass(frozen=True)
class OrderCreationResult:
    order: Order
    created: bool


def validate_products_availability(items, *, lock=False):
    product_ids = [item['product_id'] for item in items]
    queryset = Product.all_objects.select_related('category').filter(
        pk__in=product_ids,
    )
    if lock:
        queryset = queryset.select_for_update()

    products_by_id = {product.pk: product for product in queryset}
    errors = []

    for product_id in product_ids:
        product = products_by_id.get(product_id)
        if (
            product is None
            or product.status != StatusProduct.ACTIVO
            or product.category.status != Category.Status.ACTIVO
        ):
            errors.append({
                'product_id': product_id,
                'code': PRODUCT_NOT_FOUND,
                'message': 'El producto fue eliminado o no existe.',
            })
        elif not product.available:
            errors.append({
                'product_id': product_id,
                'code': PRODUCT_INACTIVE,
                'message': 'El producto ya no está disponible.',
            })

    return products_by_id, errors


def _request_fingerprint(user, order_data, items):
    fingerprint_data = {
        'user_id': user.pk,
        'metodo_pago': order_data['metodo_pago'],
        'tipo_entrega': order_data['tipo_entrega'],
        'direccion': order_data.get('direccion'),
        'items': sorted(
            (
                {'product_id': item['product_id'], 'quantity': item['quantity']}
                for item in items
            ),
            key=lambda item: item['product_id'],
        ),
    }
    encoded = json.dumps(
        fingerprint_data,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _existing_idempotent_order(key, user, fingerprint):
    existing = Order.objects.filter(idempotency_key=key).first()
    if existing is None:
        return None
    if (
        existing.user_id != user.pk
        or existing.request_fingerprint != fingerprint
    ):
        raise IdempotencyKeyConflict
    return existing


def create_order(*, user, order_data, items, idempotency_key=None):
    fingerprint = _request_fingerprint(user, order_data, items)

    try:
        with transaction.atomic():
            products_by_id, errors = validate_products_availability(
                items,
                lock=True,
            )
            if errors:
                raise UnavailableProductsError(errors)

            if idempotency_key:
                existing = _existing_idempotent_order(
                    idempotency_key,
                    user,
                    fingerprint,
                )
                if existing:
                    return OrderCreationResult(existing, created=False)

            order = Order.objects.create(
                user=user,
                idempotency_key=idempotency_key or None,
                request_fingerprint=fingerprint,
                **order_data,
            )
            pending_status, _ = Status.objects.get_or_create(
                name=Status.PENDIENTE,
            )

            total = 0
            product_names = []
            notification_products = []
            product_quantity = 0

            for item in items:
                product = products_by_id[item['product_id']]
                quantity = item['quantity']
                item_subtotal = product.price * quantity

                DetailOrder.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    subtotal=item_subtotal,
                    status=pending_status,
                )

                total += item_subtotal
                product_names.append(product.name)
                notification_products.append({
                    'name': product.name,
                    'quantity': quantity,
                    'unit_price': str(product.price),
                    'subtotal': str(item_subtotal),
                })
                product_quantity += quantity

            order.subtotal = total
            order.total = total
            order.save(update_fields=['subtotal', 'total'])

            notification_data = {
                'order_id': order.pk,
                'user_id': user.pk,
                'product_name': ', '.join(product_names),
                'products': notification_products,
                'order_date': order.fecha.strftime('%d/%m/%Y'),
                'order_time': order.hora.strftime('%H:%M'),
                'customer_name': (
                    f'{getattr(user, "nombres", "") or user.email} '
                    f'{getattr(user, "apellidos", "") or ""}'
                ).strip(),
                'product_quantity': product_quantity,
                'payment_method': order.get_metodo_pago_display(),
                'delivery_type': order.get_tipo_entrega_display(),
                'total': str(order.total),
                'status': order.status,
            }
            transaction.on_commit(
                lambda data=notification_data: publish_order_update(**data)
            )

            return OrderCreationResult(order, created=True)
    except IntegrityError:
        if not idempotency_key:
            raise
        existing = _existing_idempotent_order(
            idempotency_key,
            user,
            fingerprint,
        )
        if existing is None:
            raise
        return OrderCreationResult(existing, created=False)
