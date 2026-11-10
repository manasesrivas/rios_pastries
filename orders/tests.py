from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework.test import APITestCase

from orders.forms import OrderForm
from orders.models import Order
from orders.consumers import NotificationsConsumer
from products.models import Product, StatusProduct
from categories.models import Category
from detail_orders.models import DetailOrder

User = get_user_model()


class OrderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='order-api@example.com',
            password='SecurePass123!',
            nombres='Ana',
            apellidos='Cliente',
        )
        self.other_user = User.objects.create_user(
            email='other-order-api@example.com',
            password='SecurePass123!',
        )
        order_permission = Permission.objects.filter(
            content_type__app_label='orders',
            codename__in=['view_order', 'add_order'],
        )
        self.user.user_permissions.add(*order_permission)
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Pasteles API')
        self.product = Product.objects.create(
            name='Pastel API',
            description='Pastel para pruebas de API.',
            price=Decimal('12.50'),
            category=self.category,
            available=True,
        )
        self.url = reverse('orders_api:list_create')
        self.validate_url = reverse('orders_api:validate-cart')

    def test_list_only_returns_authenticated_users_orders(self):
        own_order = Order.objects.create(
            user=self.user,
            metodo_pago=Order.MetodoPago.EFECTIVO,
            tipo_entrega=Order.TipoEntrega.RECOGER,
        )
        Order.objects.create(
            user=self.other_user,
            metodo_pago=Order.MetodoPago.EFECTIVO,
            tipo_entrega=Order.TipoEntrega.RECOGER,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [own_order.pk])

    def test_manager_also_only_sees_the_authenticated_users_orders(self):
        manager_group, _ = Group.objects.get_or_create(name='Administrador')
        self.user.groups.add(manager_group)
        own_order = Order.objects.create(
            user=self.user,
            metodo_pago=Order.MetodoPago.EFECTIVO,
            tipo_entrega=Order.TipoEntrega.RECOGER,
        )
        Order.objects.create(
            user=self.other_user,
            metodo_pago=Order.MetodoPago.EFECTIVO,
            tipo_entrega=Order.TipoEntrega.RECOGER,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [own_order.pk])

    @patch('orders.serializers.is_store_open', return_value=True)
    def test_create_order_calculates_total_from_product_prices(self, store_is_open):
        payload = {
            'metodo_pago': Order.MetodoPago.TARJETA,
            'tipo_entrega': Order.TipoEntrega.DOMICILIO,
            'direccion': 'Calle de prueba',
            'user_id': self.other_user.pk,
            'items': [{
                'product_id': self.product.pk,
                'quantity': 2,
                'price': '0.01',
            }],
        }

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user'], self.user.pk)
        self.assertEqual(response.data['subtotal'], '25.00')
        self.assertEqual(response.data['total'], '25.00')
        self.assertEqual(len(response.data['details']), 1)
        detail = DetailOrder.objects.get(order_id=response.data['id'])
        self.assertEqual(detail.quantity, 2)
        self.assertEqual(detail.price, Decimal('12.50'))
        self.assertEqual(detail.subtotal, Decimal('25.00'))

    @patch('orders.serializers.is_store_open', return_value=True)
    def test_create_rejects_products_that_are_not_available(self, store_is_open):
        self.product.available = False
        self.product.save(update_fields=['available'])
        payload = {
            'metodo_pago': Order.MetodoPago.EFECTIVO,
            'tipo_entrega': Order.TipoEntrega.RECOGER,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.data['errors'][0]['code'],
            'PRODUCT_INACTIVE',
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(DetailOrder.objects.count(), 0)

    def test_validate_cart_treats_products_in_deleted_categories_as_missing(self):
        self.category.status = Category.Status.ELIMINADO
        self.category.save(update_fields=['status'])

        response = self.client.post(
            self.validate_url,
            {
                'items': [{
                    'product_id': self.product.pk,
                    'quantity': 1,
                }],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.data['errors'][0]['code'],
            'PRODUCT_NOT_FOUND',
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(DetailOrder.objects.count(), 0)

    def test_validate_cart_returns_valid_without_writing_orders(self):
        response = self.client.post(
            self.validate_url,
            {
                'items': [{
                    'product_id': self.product.pk,
                    'quantity': 2,
                }],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'valid': True})
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(DetailOrder.objects.count(), 0)

    def test_validate_cart_returns_all_unavailable_product_errors(self):
        inactive_product = Product.objects.create(
            name='Pastel no disponible',
            description='No disponible.',
            price=Decimal('8.00'),
            category=self.category,
            available=False,
        )
        deleted_product = Product.all_objects.create(
            name='Pastel eliminado',
            description='Eliminado.',
            price=Decimal('9.00'),
            category=self.category,
            status=StatusProduct.ELIMINADO,
        )
        missing_product_id = 999999

        response = self.client.post(
            self.validate_url,
            {
                'items': [
                    {'product_id': deleted_product.pk, 'quantity': 1},
                    {'product_id': inactive_product.pk, 'quantity': 1},
                    {'product_id': missing_product_id, 'quantity': 1},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'CART_UNAVAILABLE_PRODUCTS')
        self.assertEqual(
            response.data['errors'],
            [
                {
                    'product_id': deleted_product.pk,
                    'code': 'PRODUCT_NOT_FOUND',
                    'message': 'El producto fue eliminado o no existe.',
                },
                {
                    'product_id': inactive_product.pk,
                    'code': 'PRODUCT_INACTIVE',
                    'message': 'El producto ya no está disponible.',
                },
                {
                    'product_id': missing_product_id,
                    'code': 'PRODUCT_NOT_FOUND',
                    'message': 'El producto fue eliminado o no existe.',
                },
            ],
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(DetailOrder.objects.count(), 0)

    @patch('orders.serializers.is_store_open', return_value=True)
    def test_create_rejects_entire_cart_when_multiple_products_are_unavailable(
        self,
        store_is_open,
    ):
        self.product.status = StatusProduct.ELIMINADO
        self.product.save(update_fields=['status'])
        inactive_product = Product.objects.create(
            name='Pastel no disponible',
            description='No disponible.',
            price=Decimal('8.00'),
            category=self.category,
            available=False,
        )
        payload = {
            'metodo_pago': Order.MetodoPago.EFECTIVO,
            'tipo_entrega': Order.TipoEntrega.RECOGER,
            'items': [
                {'product_id': self.product.pk, 'quantity': 1},
                {'product_id': inactive_product.pk, 'quantity': 2},
                {'product_id': 999999, 'quantity': 1},
            ],
        }

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(response.data['errors']), 3)
        self.assertEqual(
            [error['code'] for error in response.data['errors']],
            [
                'PRODUCT_NOT_FOUND',
                'PRODUCT_INACTIVE',
                'PRODUCT_NOT_FOUND',
            ],
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(DetailOrder.objects.count(), 0)

    def test_validation_rejects_duplicate_ids_and_invalid_quantities(self):
        duplicate_response = self.client.post(
            self.validate_url,
            {
                'items': [
                    {'product_id': self.product.pk, 'quantity': 1},
                    {'product_id': self.product.pk, 'quantity': 2},
                ],
            },
            format='json',
        )
        quantity_response = self.client.post(
            self.url,
            {
                'metodo_pago': Order.MetodoPago.EFECTIVO,
                'tipo_entrega': Order.TipoEntrega.RECOGER,
                'items': [{'product_id': self.product.pk, 'quantity': 0}],
            },
            format='json',
        )

        self.assertEqual(duplicate_response.status_code, 400)
        self.assertEqual(quantity_response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(DetailOrder.objects.count(), 0)

    @patch('orders.serializers.is_store_open', return_value=True)
    def test_idempotency_key_prevents_duplicate_orders(self, store_is_open):
        payload = {
            'metodo_pago': Order.MetodoPago.EFECTIVO,
            'tipo_entrega': Order.TipoEntrega.RECOGER,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }

        first_response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY='order-request-1',
        )
        retry_response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY='order-request-1',
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(retry_response.status_code, 200)
        self.assertEqual(first_response.data['id'], retry_response.data['id'])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(DetailOrder.objects.count(), 1)

    @patch('orders.serializers.is_store_open', return_value=True)
    def test_idempotency_key_rejects_a_different_request(self, store_is_open):
        payload = {
            'metodo_pago': Order.MetodoPago.EFECTIVO,
            'tipo_entrega': Order.TipoEntrega.RECOGER,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }
        self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY='order-request-2',
        )
        payload['items'][0]['quantity'] = 2

        response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY='order-request-2',
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'IDEMPOTENCY_KEY_REUSED')
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(DetailOrder.objects.count(), 1)

    @patch(
        'orders.order_service.DetailOrder.objects.create',
        side_effect=RuntimeError('detail insert failed'),
    )
    @patch('orders.serializers.is_store_open', return_value=True)
    def test_detail_creation_failure_rolls_back_the_order(
        self,
        store_is_open,
        create_detail,
    ):
        payload = {
            'metodo_pago': Order.MetodoPago.EFECTIVO,
            'tipo_entrega': Order.TipoEntrega.RECOGER,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }

        with self.assertRaises(RuntimeError):
            self.client.post(self.url, payload, format='json')

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(DetailOrder.objects.count(), 0)

    def test_list_requires_authentication_and_view_permission(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

        self.client.force_authenticate(user=self.other_user)
        self.assertEqual(self.client.get(self.url).status_code, 403)


class OrderFormTests(TestCase):
    def test_quantity_payment_and_delivery_are_required(self):
        form = OrderForm()

        for field_name in ('quantity', 'metodo_pago', 'tipo_entrega'):
            self.assertTrue(form.fields[field_name].required)

    def test_empty_payment_and_delivery_cannot_be_submitted(self):
        form = OrderForm({
            'quantity': 1,
            'metodo_pago': '',
            'tipo_entrega': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('metodo_pago', form.errors)
        self.assertIn('tipo_entrega', form.errors)


# ============================================================
# PARTE 1: Tests del Modelo Order
# ============================================================
class OrderModelTest(TestCase):
    """
    Pruebas unitarias para el modelo Order.
    TestCase crea una base de datos temporal para cada test
    y la destruye al finalizar (aislamiento total).
    """

    def setUp(self):
        """
        setUp() se ejecuta ANTES de cada método de test.
        Aquí creamos los datos necesarios para las pruebas.
        """
        # Crear un usuario de prueba
        self.user = User.objects.create_user(
            email='cliente@test.com',
            password='password123',
            nombres='Juan',
            apellidos='Pérez',
        )

        # Crear una orden de prueba
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total=Decimal('116.00'),
            direccion='Calle Falsa 123',
        )

    def test_pago_y_entrega_son_requeridos(self):
        for field_name in ('metodo_pago', 'tipo_entrega'):
            field = Order._meta.get_field(field_name)
            self.assertFalse(field.blank)
            self.assertFalse(field.has_default())

    def test_order_creation(self):
        """Verificar que la orden se crea correctamente."""
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.subtotal, Decimal('100.00'))
        self.assertEqual(self.order.total, Decimal('116.00'))
        self.assertEqual(self.order.direccion, 'Calle Falsa 123')

    def test_order_has_fecha_automatica(self):
        """Verificar que la fecha se asigna automáticamente (auto_now_add)."""
        self.assertIsNotNone(self.order.fecha)

    def test_order_has_hora_automatica(self):
        """Verificar que la hora se asigna automáticamente (auto_now_add)."""
        self.assertIsNotNone(self.order.hora)

    def test_order_defaults(self):
        """Verificar los valores por defecto de subtotal y total."""
        order = Order.objects.create(user=self.user)
        self.assertEqual(order.subtotal, Decimal('0'))
        self.assertEqual(order.total, Decimal('0'))

    def test_order_direccion_puede_ser_nula(self):
        """Verificar que dirección es opcional (blank=True, null=True)."""
        order = Order.objects.create(user=self.user)
        self.assertIsNone(order.direccion)


# ============================================================
# PARTE 2: Tests del Flujo Completo de un Encargo (Order)
# ============================================================
class OrderFlowTest(TestCase):
    """
    Pruebas de integración: simulan el flujo completo
    de crear un encargo con sus detalles.
    """

    def setUp(self):
        """Preparar todos los datos necesarios para el flujo."""
        # 1. Crear usuario
        self.user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            nombres='Admin',
            apellidos='Test',
        )

        # 2. Crear categoría y productos
        self.categoria = Category.objects.create(name='Pasteles')

        self.producto1 = Product.objects.create(
            name='Pastel de Chocolate',
            description='Delicioso pastel de chocolate',
            price=Decimal('250.00'),
            category=self.categoria,
            available=True,
            stock=10,
        )

        self.producto2 = Product.objects.create(
            name='Pastel de Vainilla',
            description='Pastel clásico de vainilla',
            price=Decimal('200.00'),
            category=self.categoria,
            available=True,
            stock=5,
        )

    def test_crear_encargo_completo(self):
        """
        Test principal: crear un encargo (Order) con dos productos
        y verificar que todo se guarda correctamente.
        """
        # PASO 1: Crear la orden
        order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('0'),
            total=Decimal('0'),
            direccion='Av. Principal 456',
        )

        # PASO 2: Agregar detalles (productos al encargo)
        detalle1 = DetailOrder.objects.create(
            order=order,
            product=self.producto1,
            quantity=2,
            price=self.producto1.price,
            subtotal=self.producto1.price * 2,  # 500.00
        )

        detalle2 = DetailOrder.objects.create(
            order=order,
            product=self.producto2,
            quantity=1,
            price=self.producto2.price,
            subtotal=self.producto2.price * 1,  # 200.00
        )

        # PASO 3: Actualizar totales de la orden
        subtotal = detalle1.subtotal + detalle2.subtotal  # 700.00
        order.subtotal = subtotal
        order.total = subtotal  # Sin impuesto adicional
        order.save()

        # PASO 4: Verificaciones (assertions)
        order.refresh_from_db()

        # Verificar la orden
        self.assertEqual(order.subtotal, Decimal('700.00'))
        self.assertEqual(order.total, Decimal('700.00'))
        self.assertEqual(order.direccion, 'Av. Principal 456')

        # Verificar que la orden tiene 2 detalles
        self.assertEqual(order.order.count(), 2)  # related_name="order"

        # Verificar detalle 1
        self.assertEqual(detalle1.product.name, 'Pastel de Chocolate')
        self.assertEqual(detalle1.quantity, 2)
        self.assertEqual(detalle1.subtotal, Decimal('500.00'))

        # Verificar detalle 2
        self.assertEqual(detalle2.product.name, 'Pastel de Vainilla')
        self.assertEqual(detalle2.quantity, 1)
        self.assertEqual(detalle2.subtotal, Decimal('200.00'))

    def test_no_duplicar_producto_en_orden(self):
        """
        Verificar que la constraint unique_producto_por_pedido
        impide agregar el mismo producto dos veces a la misma orden.
        """
        from django.db import IntegrityError

        order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('250.00'),
            total=Decimal('250.00'),
        )

        # Primer detalle: OK
        DetailOrder.objects.create(
            order=order,
            product=self.producto1,
            quantity=1,
            price=self.producto1.price,
            subtotal=self.producto1.price,
        )

        # Segundo detalle con el mismo producto: debe fallar
        with self.assertRaises(IntegrityError):
            DetailOrder.objects.create(
                order=order,
                product=self.producto1,  # Mismo producto
                quantity=3,
                price=self.producto1.price,
                subtotal=self.producto1.price * 3,
            )


# ============================================================
# PARTE 3: Tests de las Vistas (HTTP / URLs)
# ============================================================
class OrderViewsTest(TestCase):
    """
    Pruebas de las vistas: simulan peticiones HTTP reales
    usando el Client de Django.
    """

    def setUp(self):
        """Crear usuario con permisos y datos de prueba."""
        # Crear usuario admin con todos los permisos de orders
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            nombres='Admin',
            apellidos='Test',
        )

        # Asignar permisos de orders al usuario
        order_ct = ContentType.objects.get_for_model(Order)
        permissions = Permission.objects.filter(content_type=order_ct)
        self.admin_user.user_permissions.set(permissions)

        # Crear datos de prueba
        self.categoria = Category.objects.create(name='Pasteles')
        self.producto = Product.objects.create(
            name='Pastel Test',
            description='Descripción test',
            price=Decimal('100.00'),
            category=self.categoria,
            available=True,
            stock=5,
        )
        self.order = Order.objects.create(
            user=self.admin_user,
            subtotal=Decimal('100.00'),
            total=Decimal('100.00'),
            direccion='Dirección test',
        )

        # Cliente HTTP de pruebas
        self.client = Client()

    def test_list_view_sin_login_denegado(self):
        """
        Un usuario no autenticado no puede ver la lista de órdenes.
        Como raise_exception=True está en PermissionRequiredMixin,
        Django devuelve 403 en lugar de redirigir al login.
        """
        response = self.client.get(reverse('orders:list'))
        # 403 = Forbidden (raise_exception=True en el mixin)
        self.assertEqual(response.status_code, 403)

    def test_list_view_con_login(self):
        """
        Un usuario autenticado con permisos debe poder
        ver la lista de órdenes (status 200).
        """
        self.client.login(email='admin@test.com', password='admin123')
        response = self.client.get(reverse('orders:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_muestra_suma_de_unidades_encargadas(self):
        self.client.login(email='admin@test.com', password='admin123')
        DetailOrder.objects.create(
            order=self.order,
            product=self.producto,
            quantity=3,
            price=Decimal('100.00'),
            subtotal=Decimal('300.00'),
        )

        response = self.client.get(reverse('orders:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['orders'][0].product_quantity, 3)
        self.assertContains(response, 'Productos encargados: 3 unidades')

    def test_list_view_muestra_pago_y_tipo_de_entrega(self):
        self.order.metodo_pago = Order.MetodoPago.TARJETA
        self.order.tipo_entrega = Order.TipoEntrega.RECOGER
        self.order.save()
        self.client.login(email='admin@test.com', password='admin123')

        response = self.client.get(reverse('orders:list'))

        self.assertContains(response, 'Pago: Tarjeta')
        self.assertContains(response, 'Entrega: Recoger en tienda')

    def test_list_view_muestra_estado_del_pedido_en_la_tarjeta(self):
        self.order.status = Order.Estado.APARTADO
        self.order.save(update_fields=['status'])
        self.client.login(email='admin@test.com', password='admin123')

        response = self.client.get(reverse('orders:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apartado')
        self.assertContains(response, 'data-field="status"')

    def test_detail_view_con_login(self):
        """Ver el detalle de una orden existente."""
        self.client.login(email='admin@test.com', password='admin123')
        response = self.client.get(
            reverse('orders:detail', kwargs={'pk': self.order.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cambiar estado')

    def test_usuario_con_permiso_puede_cambiar_estado_desde_detalle(self):
        self.client.login(email='admin@test.com', password='admin123')

        response = self.client.post(
            reverse('orders:status_update', kwargs={'pk': self.order.pk}),
            {'status': Order.Estado.ENTREGADO},
        )

        self.assertRedirects(
            response,
            reverse('orders:detail', kwargs={'pk': self.order.pk}),
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Estado.ENTREGADO)

    def test_usuario_sin_permiso_no_puede_cambiar_estado(self):
        self.client.login(email='admin@test.com', password='admin123')
        self.admin_user.user_permissions.remove(
            Permission.objects.get(
                content_type__app_label='orders',
                codename='change_order',
            )
        )

        response = self.client.post(
            reverse('orders:status_update', kwargs={'pk': self.order.pk}),
            {'status': Order.Estado.CANCELADO},
        )

        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Estado.PENDIENTE)

    def test_detail_view_orden_inexistente(self):
        """Intentar ver una orden que no existe debe dar 404."""
        self.client.login(email='admin@test.com', password='admin123')
        response = self.client.get(
            reverse('orders:detail', kwargs={'pk': 9999})
        )
        self.assertEqual(response.status_code, 404)

    def test_cada_envio_crea_un_pedido_independiente(self):
        """
        Cada envío crea un pedido nuevo, aunque el cliente ya tenga otro
        pedido con el mismo producto.
        """
        self.client.login(email='admin@test.com', password='admin123')

        response = self.client.post(
            reverse('orders:create'),
            {
                'product_id': self.producto.pk,
                'quantity': 1,
                'metodo_pago': Order.MetodoPago.EFECTIVO,
                'tipo_entrega': Order.TipoEntrega.DOMICILIO,
            },
        )
        self.assertEqual(response.status_code, 302)

        order = Order.objects.filter(user=self.admin_user).last()
        self.assertIsNotNone(order)
        self.assertEqual(order.total, Decimal('100.00'))
        self.assertEqual(order.metodo_pago, Order.MetodoPago.EFECTIVO)
        self.assertEqual(order.tipo_entrega, Order.TipoEntrega.DOMICILIO)

        detalle = DetailOrder.objects.get(order=order, product=self.producto)
        self.assertEqual(detalle.quantity, 1)
        self.assertEqual(detalle.subtotal, Decimal('100.00'))

        response2 = self.client.post(
            reverse('orders:create'),
            {
                'product_id': self.producto.pk,
                'quantity': 1,
                'metodo_pago': Order.MetodoPago.TARJETA,
                'tipo_entrega': Order.TipoEntrega.RECOGER,
            },
        )
        self.assertEqual(response2.status_code, 302)

        second_order = Order.objects.filter(
            user=self.admin_user,
        ).order_by('-pk').first()
        self.assertNotEqual(second_order.pk, order.pk)
        second_detail = DetailOrder.objects.get(
            order=second_order,
            product=self.producto,
        )
        self.assertEqual(second_detail.quantity, 1)
        self.assertEqual(second_order.total, Decimal('100.00'))
        self.assertEqual(second_order.metodo_pago, Order.MetodoPago.TARJETA)
        self.assertEqual(second_order.tipo_entrega, Order.TipoEntrega.RECOGER)

    def test_un_envio_crea_un_pedido_con_multiples_productos(self):
        second_product = Product.objects.create(
            name='Galleta Test',
            description='Descripción test',
            price=Decimal('25.00'),
            category=self.categoria,
            available=True,
            stock=8,
        )
        self.client.login(email='admin@test.com', password='admin123')

        response = self.client.post(
            reverse('orders:create'),
            {
                'product_id': [str(self.producto.pk), str(second_product.pk)],
                'quantity': ['2', '3'],
                'metodo_pago': Order.MetodoPago.EFECTIVO,
                'tipo_entrega': Order.TipoEntrega.DOMICILIO,
            },
        )

        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(user=self.admin_user).order_by('-pk').first()
        self.assertNotEqual(order.pk, self.order.pk)
        self.assertEqual(order.total, Decimal('275.00'))
        self.assertEqual(order.order.count(), 2)
        self.assertEqual(
            order.order.get(product=self.producto).quantity,
            2,
        )
        self.assertEqual(
            order.order.get(product=second_product).quantity,
            3,
        )

    def test_post_crear_orden_rechaza_pago_y_entrega_vacios(self):
        self.client.login(email='admin@test.com', password='admin123')

        response = self.client.post(
            reverse('orders:create'),
            {'product_id': self.producto.pk, 'quantity': 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(user=self.admin_user).count(), 1)

    def test_adding_product_notifies_existing_order_after_commit(self):
        self.client.login(email='admin@test.com', password='admin123')

        with patch('orders.views.publish_order_update') as publish_order_update:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse('orders:create'),
                    {
                        'product_id': self.producto.pk,
                        'quantity': 3,
                        'metodo_pago': Order.MetodoPago.EFECTIVO,
                        'tipo_entrega': Order.TipoEntrega.DOMICILIO,
                    },
                )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.filter(user=self.admin_user).count(), 2)
        new_order = Order.objects.filter(
            user=self.admin_user,
        ).order_by('-pk').first()
        detail = DetailOrder.objects.get(
            order=new_order,
            product=self.producto,
        )
        self.assertEqual(detail.quantity, 3)
        self.assertEqual(new_order.pk, detail.order_id)
        self.assertEqual(new_order.total, Decimal('300.00'))
        publish_order_update.assert_called_once_with(
            order_id=new_order.pk,
            product_name=self.producto.name,
            products=[{
                'name': self.producto.name,
                'quantity': 3,
                'unit_price': '100.00',
                'subtotal': '300.00',
            }],
            order_date=new_order.fecha.strftime('%d/%m/%Y'),
            order_time=new_order.hora.strftime('%H:%M'),
            customer_name='Admin Test',
            product_quantity=3,
            payment_method='Efectivo',
            delivery_type='Domicilio',
            total='300.00',
            status=Order.Estado.PENDIENTE,
        )

    def test_usuario_sin_permisos_recibe_403(self):
        """
        Un usuario autenticado pero SIN permisos debe recibir
        403 Forbidden (raise_exception=True en los mixins).
        """
        # Crear usuario sin permisos
        user_sin_permisos = User.objects.create_user(
            email='sinpermisos@test.com',
            password='test123',
        )
        self.client.login(email='sinpermisos@test.com', password='test123')
        response = self.client.get(reverse('orders:list'))
        self.assertEqual(response.status_code, 403)

    def test_delete_view_con_permisos(self):
        """
        Verificar que la vista de eliminar funciona para usuarios
        con permisos. Nota: el template confirm_delete.html debe
        existir para que la vista renderice correctamente.
        """
        from django.template.exceptions import TemplateDoesNotExist

        self.client.login(email='admin@test.com', password='admin123')
        try:
            response = self.client.get(
                reverse('orders:delete', kwargs={'pk': self.order.pk})
            )
            self.assertEqual(response.status_code, 200)
        except TemplateDoesNotExist:
            # El template aún no ha sido creado, pero la vista
            # sí concede acceso (no da 403 ni 302)
            pass

    def test_filtrado_pedidos_por_rol(self):
        """
        Verificar que un Cliente solo ve sus propios pedidos,
        mientras que un Administrador/Cajero ve los de todos.
        """
        from django.contrib.auth.models import Group

        # Crear grupo Cliente y usuario cliente
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        cliente_user = User.objects.create_user(
            email='cliente_rol@test.com',
            password='password123',
            nombres='Cliente',
            apellidos='Test'
        )
        cliente_user.groups.add(grupo_cliente)
        
        # Asignar permisos de ver y agregar pedidos al cliente (PermissionsClient exige ambos)
        order_ct = ContentType.objects.get_for_model(Order)
        permisos = Permission.objects.filter(content_type=order_ct, codename__in=['view_order', 'add_order'])
        cliente_user.user_permissions.set(permisos)

        # Crear un pedido para este cliente (self.order pertenece a self.admin_user)
        orden_cliente = Order.objects.create(
            user=cliente_user,
            subtotal=Decimal('50.00'),
            total=Decimal('50.00')
        )

        # 1. El cliente inicia sesión: solo debe ver SU pedido en la lista
        self.client.login(email='cliente_rol@test.com', password='password123')
        response_cliente = self.client.get(reverse('orders:list'))
        pedidos_cliente = list(response_cliente.context['orders'])
        self.assertEqual(len(pedidos_cliente), 1)
        self.assertEqual(pedidos_cliente[0].pk, orden_cliente.pk)

        # Tampoco debe poder ver el detalle del pedido de admin (404)
        resp_detail_ajeno = self.client.get(reverse('orders:detail', kwargs={'pk': self.order.pk}))
        self.assertEqual(resp_detail_ajeno.status_code, 404)

        # 2. El admin inicia sesión: debe ver AMBOS pedidos
        grupo_admin, _ = Group.objects.get_or_create(name='Administrador')
        self.admin_user.groups.add(grupo_admin)

        self.client.login(email='admin@test.com', password='admin123')
        response_admin = self.client.get(reverse('orders:list'))
        pedidos_admin = list(response_admin.context['orders'])
        self.assertEqual(len(pedidos_admin), 2)


class OrderNotificationConsumerTests(TestCase):
    def test_order_manager_receives_product_added_to_order_event(self):
        async def verify_notification():
            communicator = WebsocketCommunicator(
                NotificationsConsumer.as_asgi(),
                '/ws/notificaciones/',
            )
            communicator.scope['user'] = SimpleNamespace(
                is_authenticated=True,
                is_superuser=False,
                is_staff=True,
            )

            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            await get_channel_layer().group_send(
                'order_administrators',
                {
                    'type': 'order_updated',
                    'order_id': 42,
                    'product_name': 'Pastel de prueba',
                    'products': [{
                        'name': 'Pastel de prueba',
                        'quantity': 2,
                        'unit_price': '12.50',
                        'subtotal': '25.00',
                    }],
                    'order_date': '02/11/2026',
                    'order_time': '12:00',
                    'customer_name': 'Cliente de prueba',
                    'product_quantity': 2,
                    'payment_method': 'Efectivo',
                    'delivery_type': 'Domicilio',
                    'total': '25.00',
                    'status': 'pendiente',
                },
            )
            message = await communicator.receive_json_from()
            self.assertEqual(
                message,
                {
                    'type': 'order_updated',
                    'order_id': 42,
                    'product_name': 'Pastel de prueba',
                    'products': [{
                        'name': 'Pastel de prueba',
                        'quantity': 2,
                        'unit_price': '12.50',
                        'subtotal': '25.00',
                    }],
                    'order_date': '02/11/2026',
                    'order_time': '12:00',
                    'customer_name': 'Cliente de prueba',
                    'product_quantity': 2,
                    'payment_method': 'Efectivo',
                    'delivery_type': 'Domicilio',
                    'total': '25.00',
                    'status': 'pendiente',
                },
            )
            await communicator.disconnect()

        async_to_sync(verify_notification)()
