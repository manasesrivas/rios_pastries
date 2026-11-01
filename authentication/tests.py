from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
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
