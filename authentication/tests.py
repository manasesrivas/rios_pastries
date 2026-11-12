from unittest.mock import patch
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import LoginForm, UserRegisterForm


class LoginFormTests(TestCase):
    def test_login_fields_include_tailwind_classes(self):
        form = LoginForm()

        self.assertIn('focus:ring-2', form.fields['email'].widget.attrs['class'])
        self.assertIn('focus:ring-2', form.fields['password'].widget.attrs['class'])

    def test_login_page_renders_form_and_tailwind_styles(self):
        response = self.client.get(reverse('authentication:login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar sesión')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'bg-indigo-600')
        self.assertContains(response, 'css/dist/styles.css')


class UserRegisterFormTests(TestCase):
    @patch('authentication.views.send_verification_email')
    def test_registration_saves_user_as_inactive(self, send_verification_email):
        Group.objects.get_or_create(name='Cliente')

        response = self.client.post(reverse('authentication:register'), {
            'nombres': 'Ana',
            'apellidos': 'Rivas',
            'email': 'ana@example.com',
            'telefono': '1234-5678',
            'direccion': 'Calle principal',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })

        user = get_user_model().objects.get(email='ana@example.com')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.is_active)
        send_verification_email.assert_called_once()

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        STORAGES={
            'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            },
        },
    )
    def test_web_registration_requires_email_activation_before_login(self):
        Group.objects.get_or_create(name='Cliente')
        credentials = {'email': 'verify@example.com', 'password': 'ComplexPass123!'}
        response = self.client.post(reverse('authentication:register'), {
            'nombres': 'Ana',
            'apellidos': 'Rivas',
            'email': credentials['email'],
            'telefono': '1234-5678',
            'direccion': 'Calle principal',
            'password1': credentials['password'],
            'password2': credentials['password'],
        })

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email=credentials['email'])
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

        admin = get_user_model().objects.create_superuser(
            email='admin@example.com', password='AdminPass123!',
        )
        admin_client = Client()
        admin_client.force_login(admin)
        listing = admin_client.get(reverse('users:list'))
        self.assertContains(listing, user.email)
        self.assertContains(listing, '<td class="px-6 py-4">Deshabilitado</td>', html=True)
        detail = admin_client.get(reverse('users:detail', args=[user.pk]))
        self.assertContains(detail, 'Deshabilitado')
        admin_listing = admin_client.get(reverse('admin:users_user_changelist'))
        self.assertContains(admin_listing, 'Acceso habilitado')
        self.assertContains(admin_listing, 'icon-no.svg')

        response = self.client.post(reverse('authentication:login'), credentials)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        activation_url = next(
            line.strip() for line in mail.outbox[0].body.splitlines()
            if '/activate/' in line
        )
        response = self.client.get(urlsplit(activation_url).path)
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        listing = admin_client.get(reverse('users:list'))
        self.assertContains(listing, '<td class="px-6 py-4">Habilitado</td>', html=True)

        self.client.logout()
        response = self.client.post(reverse('authentication:login'), credentials)
        self.assertRedirects(response, reverse('users:home'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_fields_include_tailwind_classes(self):
        form = UserRegisterForm()

        for field in form.fields.values():
            self.assertIn('focus:ring-2', field.widget.attrs['class'])

    def test_registration_page_renders_form_and_login_link(self):
        response = self.client.get(reverse('authentication:register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear cuenta')
        self.assertContains(response, 'name="nombres"')
        self.assertContains(response, 'name="apellidos"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')
        self.assertContains(response, reverse('authentication:login'))

    def test_base_shows_authenticated_user_name_and_group(self):
        user = get_user_model().objects.create(
            email='user@example.com',
            nombres='Ana',
            apellidos='Rivas',
        )
        group, _ = Group.objects.get_or_create(name='Cliente')
        user.groups.add(group)
        self.client.force_login(user)

        response = self.client.get(reverse('authentication:login'))

        self.assertContains(response, 'Ana Rivas')
        self.assertContains(response, 'Cliente')
        self.assertContains(response, 'assets/logo.svg')
        self.assertContains(response, 'overflow-x-auto')
        self.assertContains(response, 'Locales')
