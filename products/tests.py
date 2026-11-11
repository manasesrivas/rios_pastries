from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APITestCase

from categories.models import Category
from products.models import Product
from users.models import User


class ProductListAPITests(APITestCase):
    def test_api_lists_available_products_without_authentication(self):
        category = Category.objects.create(name='Pasteles')
        available_product = Product.objects.create(
            name='Pastel disponible',
            description='Pastel de chocolate.',
            price='12.50',
            category=category,
            available=True,
        )
        unavailable_product = Product.objects.create(
            name='Pastel no disponible',
            description='Pastel de vainilla.',
            price='10.00',
            category=category,
            available=False,
        )

        response = self.client.get(reverse('products_api:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], available_product.pk)
        self.assertEqual(response.data[0]['category'], category.pk)
        self.assertEqual(response.data[0]['price'], '12.50')

    def test_api_rejects_writes_without_authentication(self):
        response = self.client.post(reverse('products_api:list'), {})

        self.assertEqual(response.status_code, 403)


class ProductWriteAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Pasteles')
        self.product = Product.objects.create(
            name='Pastel de chocolate',
            description='Pastel artesanal.',
            price='12.50',
            category=self.category,
        )
        self.user = User.objects.create_user(
            email='product-api@example.com',
            password='SecurePass123!',
        )

    def grant_permission(self, codename):
        permission = Permission.objects.get(
            content_type__app_label='products',
            codename=codename,
        )
        self.user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user)

    def test_create_product_requires_add_permission(self):
        data = {
            'name': 'Pastel de fresa',
            'description': 'Pastel con fresas.',
            'price': '14.00',
            'category': self.category.pk,
            'available': True,
        }

        response = self.client.post(reverse('products_api:list'), data)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(name='Pastel de fresa').exists())

        self.grant_permission('add_product')
        response = self.client.post(reverse('products_api:list'), data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Pastel de fresa')

    def test_update_product_requires_change_permission(self):
        url = reverse('products_api:detail', args=[self.product.pk])
        data = {'name': 'Pastel actualizado'}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, 403)

        self.grant_permission('change_product')
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Pastel actualizado')

    def test_delete_product_requires_delete_permission(self):
        url = reverse('products_api:detail', args=[self.product.pk])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

        self.grant_permission('delete_product')
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())


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
        self.assertContains(response, '[&_input:not([type=checkbox])]:w-full')
        self.assertContains(response, '[&_textarea]:min-h-32')
        self.assertContains(response, '[&_select]:w-full')
        self.assertContains(response, '[&_input[type=checkbox]]:accent-indigo-600')


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

    def test_client_only_sees_available_products(self):
        client_group, _ = Group.objects.get_or_create(name='Cliente')
        self.user.groups.add(client_group)
        Product.objects.create(
            name='Pastel disponible',
            description='Producto disponible.',
            price='8.00',
            category=self.category,
            available=True,
        )
        Product.objects.create(
            name='Pastel no disponible',
            description='Producto no disponible.',
            price='9.00',
            category=self.category,
            available=False,
        )

        response = self.client.get(reverse('products:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pastel disponible')
        self.assertNotContains(response, 'Pastel no disponible')

    def test_non_client_can_see_unavailable_products(self):
        Product.objects.create(
            name='Pastel no disponible',
            description='Producto no disponible.',
            price='9.00',
            category=self.category,
            available=False,
        )

        response = self.client.get(reverse('products:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pastel no disponible')

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
        self.assertContains(response, 'id="quantity"')
        self.assertContains(response, 'name="quantity"')
        self.assertContains(response, 'value="1"')
        self.assertContains(response, 'data-add-to-cart')

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
