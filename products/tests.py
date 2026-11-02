from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from products.models import Product
from users.models import User


class ProductCreatePermissionTests(TestCase):
    def test_user_with_add_permission_can_open_product_creation_form(self):
        user = User.objects.create_user(
            email='product-creator@example.com',
            password='SecurePass123!',
        )
        permission = Permission.objects.get(
            content_type__app_label='products',
            codename='add_product',
        )
        user.user_permissions.add(permission)
        self.client.force_login(user)

        response = self.client.get(reverse('products:create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear producto')


class ProductListCardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='product-viewer@example.com',
            password='SecurePass123!',
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='products',
                codename='view_product',
            )
        )
        self.client.force_login(self.user)
        self.category = Category.objects.create(name='Pasteles')

    def test_product_list_displays_card_data_and_image(self):
        product = Product.objects.create(
            name='Pastel de chocolate',
            image='products/pastel-chocolate.webp',
            description='Pastel artesanal de chocolate.',
            price='12.50',
            category=self.category,
            available=True,
            stock=8,
        )
        product.refresh_from_db()

        response = self.client.get(reverse('products:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pastel de chocolate')
        self.assertContains(response, 'Pastel artesanal de chocolate.')
        self.assertContains(response, 'Pasteles')
        self.assertContains(response, '$12.50')
        self.assertContains(response, 'Existencias: 8')
        self.assertContains(response, 'Disponible')
        self.assertContains(
            response,
            f'alt="{product.name}"',
        )
        self.assertContains(response, product.image.url)

    def test_product_without_image_shows_placeholder(self):
        Product.objects.create(
            name='Pastel sin foto',
            description='Producto sin imagen asignada.',
            price='8.00',
            category=self.category,
        )

        response = self.client.get(reverse('products:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Imagen no disponible')

    def test_product_card_is_a_single_link_without_edit_or_delete_actions(self):
        product = Product.objects.create(
            name='Pastel de vainilla',
            description='Pastel de vainilla.',
            price='9.00',
            category=self.category,
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='products',
                codename='change_product',
            ),
            Permission.objects.get(
                content_type__app_label='products',
                codename='delete_product',
            ),
        )

        response = self.client.get(reverse('products:list'))

        self.assertContains(
            response,
            f'<a class="product-card" href="{reverse("products:detail", args=[product.pk])}"',
            html=False,
        )
        self.assertNotContains(response, reverse('products:update', args=[product.pk]))
        self.assertNotContains(response, reverse('products:delete', args=[product.pk]))

    def test_update_form_contains_save_and_delete_actions(self):
        product = Product.objects.create(
            name='Pastel de fresa',
            description='Pastel de fresa.',
            price='10.00',
            category=self.category,
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='products',
                codename='change_product',
            ),
            Permission.objects.get(
                content_type__app_label='products',
                codename='delete_product',
            ),
        )

        response = self.client.get(
            reverse('products:update', args=[product.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Guardar cambios')
        self.assertContains(response, 'Eliminar producto')
        self.assertContains(response, reverse('products:delete', args=[product.pk]))


class ProductDetailTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='product-detail-viewer@example.com',
            password='SecurePass123!',
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='products',
                codename='view_product',
            )
        )
        self.category = Category.objects.create(name='Pasteles')
        self.product = Product.objects.create(
            name='Pastel de chocolate',
            description='Pastel artesanal con chocolate.',
            price='12.50',
            category=self.category,
            available=True,
            stock=4,
        )
        self.client.force_login(self.user)

    def test_product_detail_displays_product_information(self):
        response = self.client.get(
            reverse('products:detail', args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pastel de chocolate')
        self.assertContains(response, 'Pasteles')
        self.assertContains(response, '$12.50')
        self.assertContains(response, 'Pastel artesanal con chocolate.')
        self.assertContains(response, '4 unidades disponibles')
        self.assertContains(response, 'Imagen no disponible')

    def test_client_can_see_order_quantity_controls(self):
        client_group, _ = Group.objects.get_or_create(name='Cliente')
        self.user.groups.add(client_group)

        response = self.client.get(
            reverse('products:detail', args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="product_id"')
        self.assertContains(response, 'name="quantity"')
        self.assertContains(response, 'Encargar producto')

    def test_user_only_sees_product_actions_they_are_allowed_to_use(self):
        change_permission = Permission.objects.get(
            content_type__app_label='products',
            codename='change_product',
        )
        self.user.user_permissions.add(change_permission)

        response = self.client.get(
            reverse('products:detail', args=[self.product.pk])
        )

        self.assertContains(response, 'Actualizar producto')
        self.assertContains(
            response,
            reverse('products:update', args=[self.product.pk]),
        )
        self.assertNotContains(response, 'Eliminar producto')
        self.assertNotContains(
            response,
            reverse('products:delete', args=[self.product.pk]),
        )

    def test_superuser_sees_update_and_delete_product_actions(self):
        self.user.is_superuser = True
        self.user.save(update_fields=['is_superuser'])

        response = self.client.get(
            reverse('products:detail', args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Actualizar producto')
        self.assertContains(
            response,
            reverse('products:update', args=[self.product.pk]),
        )
        self.assertContains(response, 'Eliminar producto')
        self.assertContains(
            response,
            reverse('products:delete', args=[self.product.pk]),
        )


class ProductDeleteConfirmationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='product-deleter@example.com',
            password='SecurePass123!',
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='products',
                codename='delete_product',
            ),
            Permission.objects.get(
                content_type__app_label='products',
                codename='view_product',
            ),
        )
        self.category = Category.objects.create(name='Pasteles')
        self.product = Product.objects.create(
            name='Pastel para eliminar',
            description='Pastel de prueba.',
            price='15.00',
            category=self.category,
        )
        self.client.force_login(self.user)

    def test_confirmation_displays_product_and_cancel_action(self):
        response = self.client.get(
            reverse('products:delete', args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pastel para eliminar')
        self.assertContains(response, 'class="delete-product-summary__content"')
        self.assertContains(response, 'class="delete-product-summary__name"')
        self.assertContains(response, 'Pasteles')
        self.assertContains(response, '$15.00')
        self.assertContains(
            response,
            'class="delete-product-warning" role="alert"',
        )
        self.assertContains(response, 'Esta acción es permanente')
        self.assertContains(
            response,
            reverse('products:detail', args=[self.product.pk]),
        )
        self.assertContains(response, 'Confirmar eliminación')

    def test_confirming_deletion_removes_product(self):
        response = self.client.post(
            reverse('products:delete', args=[self.product.pk])
        )

        self.assertRedirects(response, reverse('products:list'))
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
