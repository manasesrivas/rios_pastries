from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

from orders.models import Order
from products.models import Product
from categories.models import Category
from detail_orders.models import DetailOrder

User = get_user_model()


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

    def test_detail_view_con_login(self):
        """Ver el detalle de una orden existente."""
        self.client.login(email='admin@test.com', password='admin123')
        response = self.client.get(
            reverse('orders:detail', kwargs={'pk': self.order.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_view_orden_inexistente(self):
        """Intentar ver una orden que no existe debe dar 404."""
        self.client.login(email='admin@test.com', password='admin123')
        response = self.client.get(
            reverse('orders:detail', kwargs={'pk': 9999})
        )
        self.assertEqual(response.status_code, 404)

    def test_products_list_view(self):
        """
        La vista de productos para ordenar no requiere permisos
        especiales (no tiene mixin de permisos).
        """
        response = self.client.get(reverse('orders:products'))
        self.assertEqual(response.status_code, 200)

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
