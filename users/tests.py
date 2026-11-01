from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group, Permission

from .forms import UserProfileForm
from .models import User


class UserProfileViewTests(TestCase):
    def setUp(self):
        self.user = User(
            email='profile@example.com',
            nombres='Ana',
            apellidos='Rivas',
            telefono='1234-5678',
            is_superuser=True,
        )
        self.user.set_password('OriginalPass123!')
        self.user.save()
        self.client.force_login(self.user)

    def test_profile_displays_account_fields_without_password(self):
        response = self.client.get(reverse('users:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nombres')
        self.assertContains(response, 'Apellidos')
        self.assertContains(response, 'Teléfono')
        self.assertContains(response, 'Correo electrónico')
        self.assertContains(response, 'Ana')
        self.assertContains(response, 'profile-edit-form')
        self.assertContains(response, 'Editar perfil')
        self.assertIn('id="profile-edit-form" class="user-profile-form space-y-5" method="post" hidden', response.content.decode())
        self.assertNotIn('password', UserProfileForm().fields)

    def test_customer_profile_hides_group_and_superuser_details(self):
        customer = User.objects.create(
            email='customer-profile@example.com',
            nombres='Carla',
            apellidos='Rivas',
            telefono='2222-3333',
            is_superuser=True,
        )
        customer.groups.add(Group.objects.get(name='Cliente'))
        self.client.force_login(customer)

        response = self.client.get(reverse('users:profile'))
        profile_details = response.content.decode().split(
            'id="profile-details"',
            1,
        )[1].split('</section>', 1)[0]

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Carla')
        self.assertNotIn('>Grupo<', profile_details)
        self.assertNotIn('Superusuario', profile_details)

    def test_invalid_profile_submission_keeps_edit_form_visible(self):
        response = self.client.post(
            reverse('users:profile'),
            {
                'nombres': 'Ana',
                'apellidos': 'Rivas',
                'telefono': 'incorrecto',
                'email': 'profile@example.com',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ingresa un teléfono de exactamente 9 dígitos.')
        self.assertNotIn('id="profile-edit-form" class="user-profile-form space-y-5" method="post" hidden', response.content.decode())

    def test_profile_updates_only_the_authenticated_user_profile(self):
        original_password = self.user.password
        response = self.client.post(
            reverse('users:profile'),
            {
                'nombres': 'Ana María',
                'apellidos': 'Rivas López',
                'telefono': '2222-3333',
                'email': 'ana@example.com',
            },
        )

        self.assertRedirects(response, reverse('users:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.nombres, 'Ana María')
        self.assertEqual(self.user.email, 'ana@example.com')
        self.assertEqual(self.user.password, original_password)

    def test_user_detail_shows_only_data_and_links_to_edit_and_delete(self):
        target = User.objects.create(
            email='target@example.com',
            nombres='Luis',
            apellidos='Martínez',
            telefono='1111-2222',
        )

        response = self.client.get(reverse('users:detail', args=[target.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Luis')
        self.assertContains(response, reverse('users:update', args=[target.pk]))
        self.assertContains(response, reverse('users:delete', args=[target.pk]))
        self.assertNotContains(response, 'user-edit-form')

    def test_user_update_page_displays_the_editable_form(self):
        target = User.objects.create(
            email='target@example.com',
            nombres='Luis',
            apellidos='Martínez',
            telefono='1111-2222',
        )

        response = self.client.get(reverse('users:update', args=[target.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar usuario')
        self.assertContains(response, 'user-edit-form')
        self.assertContains(response, 'Tipo de usuario')
        self.assertNotContains(response, 'id="user-details"')

    def test_user_delete_marks_account_eliminated_without_removing_it(self):
        target = User.objects.create(
            email='target@example.com',
            nombres='Luis',
            apellidos='Martínez',
            telefono='1111-2222',
            is_active=True,
        )

        confirmation = self.client.get(reverse('users:delete', args=[target.pk]))
        self.assertEqual(confirmation.status_code, 200)
        self.assertContains(confirmation, 'Confirmar eliminación')
        self.assertTrue(User.objects.filter(pk=target.pk).exists())

        response = self.client.post(reverse('users:delete', args=[target.pk]))

        self.assertRedirects(response, reverse('users:list'))
        target.refresh_from_db()
        self.assertTrue(User.objects.filter(pk=target.pk).exists())
        self.assertEqual(target.estado, User.Estado.ELIMINADO)
        self.assertFalse(target.is_active)

    def test_deleted_user_cannot_log_in_and_superuser_can_restore_them(self):
        target = User.objects.create(
            email='target@example.com',
            nombres='Luis',
            apellidos='Martínez',
            telefono='1111-2222',
        )
        target.set_password('TargetPass123!')
        target.save()

        self.client.post(reverse('users:delete', args=[target.pk]))
        target.refresh_from_db()
        self.assertFalse(target.is_active)

        self.client.logout()
        self.assertFalse(
            self.client.login(
                email='target@example.com',
                password='TargetPass123!',
            )
        )

        self.client.force_login(self.user)
        detail = self.client.get(reverse('users:detail', args=[target.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, 'Restaurar usuario')

        response = self.client.post(reverse('users:restore', args=[target.pk]))

        self.assertRedirects(response, reverse('users:detail', args=[target.pk]))
        target.refresh_from_db()
        self.assertEqual(target.estado, User.Estado.ACTIVO)
        self.assertTrue(target.is_active)

    def test_administrator_cannot_view_deleted_user(self):
        target = User.objects.create(
            email='deleted@example.com',
            estado=User.Estado.ELIMINADO,
            is_active=False,
        )
        administrator = User.objects.create(
            email='administrator@example.com',
            is_active=True,
        )
        administrator.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='users',
            codename__in=[
                'add_user',
                'view_user',
                'change_user',
                'delete_user',
            ],
        ))
        self.client.force_login(administrator)

        listing = self.client.get(reverse('users:list'))
        detail = self.client.get(
            reverse('users:detail', args=[target.pk])
        )

        self.assertNotContains(listing, target.email)
        self.assertEqual(detail.status_code, 404)

    def test_restore_is_restricted_to_superusers(self):
        target = User.objects.create(
            email='deleted@example.com',
            estado=User.Estado.ELIMINADO,
            is_active=False,
        )
        administrator = User.objects.create(
            email='administrator@example.com',
            is_active=True,
        )
        self.client.force_login(administrator)
        self.client.raise_request_exception = False

        response = self.client.post(reverse('users:restore', args=[target.pk]))

        self.assertEqual(response.status_code, 403)
        target.refresh_from_db()
        self.assertEqual(target.estado, User.Estado.ELIMINADO)
        self.assertFalse(target.is_active)

    def test_django_admin_delete_marks_user_eliminated(self):
        target = User.objects.create(
            email='target@example.com',
            is_active=True,
        )
        administrator = User.objects.create(
            email='staff-administrator@example.com',
            is_active=True,
            is_staff=True,
        )
        administrator.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='users',
                codename='delete_user',
            )
        )
        self.client.force_login(administrator)

        response = self.client.post(
            reverse('admin:users_user_delete', args=[target.pk]),
            {'post': 'yes'},
        )

        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertTrue(User.objects.filter(pk=target.pk).exists())
        self.assertEqual(target.estado, User.Estado.ELIMINADO)
        self.assertFalse(target.is_active)

    def test_user_cannot_delete_their_own_account(self):
        self.client.raise_request_exception = False

        response = self.client.post(reverse('users:delete', args=[self.user.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_administrator_cannot_view_superuser_in_user_list_or_detail(self):
        administrator = User.objects.create(
            email='administrator@example.com',
            is_active=True,
        )
        administrator.set_password('AdminPass123!')
        administrator.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='users',
            codename__in=[
                'add_user',
                'view_user',
                'change_user',
                'delete_user',
            ],
        ))
        administrator.save()
        self.client.force_login(administrator)

        listing = self.client.get(reverse('users:list'))
        detail = self.client.get(
            reverse('users:detail', args=[self.user.pk])
        )

        self.assertEqual(listing.status_code, 200)
        self.assertNotContains(listing, self.user.email)
        self.assertEqual(detail.status_code, 404)

    def test_customer_cannot_see_or_access_user_management_even_with_permissions(self):
        customer = User.objects.create(
            email='customer@example.com',
            is_active=True,
        )
        customer.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='users',
            codename__in=[
                'add_user',
                'view_user',
                'change_user',
                'delete_user',
            ],
        ))
        customer.groups.add(Group.objects.get(name='Cliente'))
        self.client.force_login(customer)
        self.client.raise_request_exception = False

        menu = self.client.get(reverse('authentication:login'))
        listing = self.client.get(reverse('users:list'))

        self.assertNotContains(menu, 'assets/users.svg')
        self.assertEqual(listing.status_code, 403)

    def test_administrator_cannot_edit_or_delete_superuser(self):
        administrator = User.objects.create(
            email='administrator@example.com',
            is_active=True,
        )
        administrator.set_password('AdminPass123!')
        administrator.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='users',
            codename__in=[
                'add_user',
                'view_user',
                'change_user',
                'delete_user',
            ],
        ))
        administrator.save()
        self.client.force_login(administrator)

        update_url = reverse('users:update', args=[self.user.pk])
        delete_url = reverse('users:delete', args=[self.user.pk])
        self.client.raise_request_exception = False

        update_page = self.client.get(update_url)
        update_response = self.client.post(
            update_url,
            {
                'nombres': 'Modificado',
                'apellidos': 'Modificado',
                'telefono': '1111-2222',
                'email': 'modified@example.com',
                'grupo': '',
            },
        )
        delete_page = self.client.get(delete_url)
        delete_response = self.client.post(delete_url)

        self.assertEqual(update_page.status_code, 404)
        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_page.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'profile@example.com')
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_django_admin_hides_and_protects_superusers(self):
        administrator = User.objects.create(
            email='staff-administrator@example.com',
            is_active=True,
            is_staff=True,
        )
        administrator.set_password('AdminPass123!')
        administrator.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='users',
            codename__in=[
                'view_user',
                'change_user',
                'delete_user',
            ],
        ))
        administrator.save()
        self.client.force_login(administrator)

        listing = self.client.get(reverse('admin:users_user_changelist'))
        change = self.client.get(
            reverse('admin:users_user_change', args=[self.user.pk])
        )
        delete = self.client.get(
            reverse('admin:users_user_delete', args=[self.user.pk])
        )
        change_post = self.client.post(
            reverse('admin:users_user_change', args=[self.user.pk]),
            {'email': 'modified@example.com'},
        )
        delete_post = self.client.post(
            reverse('admin:users_user_delete', args=[self.user.pk]),
            {'post': 'yes'},
        )

        self.assertEqual(listing.status_code, 200)
        self.assertNotContains(listing, self.user.email)
        self.assertRedirects(change, reverse('admin:index'))
        self.assertRedirects(delete, reverse('admin:index'))
        self.assertRedirects(change_post, reverse('admin:index'))
        self.assertRedirects(delete_post, reverse('admin:index'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'profile@example.com')
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
