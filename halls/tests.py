from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APITestCase

from venues.models import Venue

from .models import Hall, HallStatus


class HallAPITests(APITestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name='Centro API',
            address='Avenida Central',
        )
        self.available_hall = Hall.objects.create(
            venue=self.venue,
            name='Salón disponible',
            capacity=50,
            price='125.00',
        )
        self.reserved_hall = Hall.objects.create(
            venue=self.venue,
            name='Salón reservado',
            capacity=30,
            price='90.00',
            status=HallStatus.RESERVADO,
        )

    def test_list_shows_available_halls_to_users_with_view_permission(self):
        user = get_user_model().objects.create_user(
            email='hall-api-reader@example.com',
            password='SecurePass123!',
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='halls',
                codename='view_hall',
            )
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse('halls_api:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [hall['id'] for hall in response.data],
            [self.available_hall.pk],
        )
        self.assertEqual(response.data[0]['venueName'], self.venue.name)
        self.assertNotIn('venue', response.data[0])

    def test_detail_shows_available_hall_and_hides_reserved_hall(self):
        user = get_user_model().objects.create_user(
            email='hall-api-detail-reader@example.com',
            password='SecurePass123!',
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='halls',
                codename='view_hall',
            )
        )
        self.client.force_authenticate(user=user)

        available_response = self.client.get(
            reverse('halls_api:detail', args=[self.available_hall.pk])
        )
        reserved_response = self.client.get(
            reverse('halls_api:detail', args=[self.reserved_hall.pk])
        )

        self.assertEqual(available_response.status_code, 200)
        self.assertEqual(available_response.data['name'], 'Salón disponible')
        self.assertEqual(available_response.data['venueName'], self.venue.name)
        self.assertNotIn('venue', available_response.data)
        self.assertEqual(reserved_response.status_code, 404)

    def test_list_and_detail_require_authentication_and_view_permission(self):
        list_url = reverse('halls_api:list')
        detail_url = reverse('halls_api:detail', args=[self.available_hall.pk])

        self.assertEqual(self.client.get(list_url).status_code, 401)
        self.assertEqual(self.client.get(detail_url).status_code, 401)

        user = get_user_model().objects.create_user(
            email='hall-api-no-permission@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=user)

        self.assertEqual(self.client.get(list_url).status_code, 403)
        self.assertEqual(self.client.get(detail_url).status_code, 403)

    def test_hall_manager_can_see_reserved_halls(self):
        manager = get_user_model().objects.create_user(
            email='hall-api-manager@example.com',
            password='SecurePass123!',
        )
        manager.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='halls',
                codename='view_hall',
            ),
            Permission.objects.get(
                content_type__app_label='halls',
                codename='change_hall',
            )
        )
        self.client.force_authenticate(user=manager)

        response = self.client.get(reverse('halls_api:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class HallViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(email='hall-list@example.com')
        self.venue = Venue.objects.create(
            name='Centro',
            address='Calle Principal',
        )
        self.available_hall = Hall.objects.create(
            venue=self.venue,
            name='Salón Norte',
            image='https://example.com/norte.jpg',
            capacity=50,
            price='125.00',
        )
        self.reserved_hall = Hall.objects.create(
            venue=self.venue,
            name='Salón Sur',
            capacity=30,
            price='90.00',
            status=HallStatus.RESERVADO,
        )

    def grant_permissions(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label='halls',
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)
        self.client.force_login(self.user)

    def test_lists_only_available_halls_for_read_only_users(self):
        self.grant_permissions('view_hall')

        response = self.client.get(reverse('halls:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['halls']), [self.available_hall])
        self.assertContains(response, 'Salón Norte')
        self.assertNotContains(response, 'Salón Sur')
        self.assertContains(response, 'https://example.com/norte.jpg')

    def test_managers_can_also_list_reserved_halls(self):
        self.grant_permissions('view_hall', 'change_hall')

        response = self.client.get(reverse('halls:list'))

        self.assertContains(response, 'Salón Sur')

    def test_menu_links_to_available_halls(self):
        self.grant_permissions('view_hall')

        response = self.client.get(reverse('halls:list'))

        self.assertContains(response, reverse('halls:list'))

    def test_detail_shows_hall_image(self):
        self.grant_permissions('view_hall')

        response = self.client.get(
            reverse('halls:detail', args=[self.available_hall.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://example.com/norte.jpg')

    def test_create_hall(self):
        self.grant_permissions('view_hall', 'add_hall')

        response = self.client.post(
            reverse('halls:create'),
            {
                'venue': self.venue.pk,
                'name': 'Salón Este',
                'capacity': 40,
                'price': '100.00',
                'status': HallStatus.DISPONIBLE,
            },
        )

        self.assertRedirects(response, reverse('halls:list'))
        self.assertTrue(Hall.objects.filter(name='Salón Este').exists())

    def test_hall_form_accepts_image_file_uploads(self):
        self.grant_permissions('view_hall', 'add_hall')

        response = self.client.get(reverse('halls:create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'type="file"')
        self.assertContains(response, 'name="image"')

    def test_update_hall(self):
        self.grant_permissions('view_hall', 'change_hall')

        response = self.client.post(
            reverse('halls:update', args=[self.available_hall.pk]),
            {
                'venue': self.venue.pk,
                'name': 'Salón Norte actualizado',
                'capacity': 60,
                'price': '150.00',
                'status': HallStatus.RESERVADO,
            },
        )

        self.assertRedirects(response, reverse('halls:list'))
        self.available_hall.refresh_from_db()
        self.assertEqual(self.available_hall.name, 'Salón Norte actualizado')
        self.assertEqual(
            self.available_hall.image,
            'https://example.com/norte.jpg',
        )

    def test_delete_hall(self):
        self.grant_permissions('view_hall', 'delete_hall')

        response = self.client.post(
            reverse('halls:delete', args=[self.available_hall.pk])
        )

        self.assertRedirects(response, reverse('halls:list'))
        self.assertFalse(Hall.objects.filter(pk=self.available_hall.pk).exists())

    def test_reserved_hall_is_hidden_from_read_only_detail(self):
        self.grant_permissions('view_hall')

        response = self.client.get(
            reverse('halls:detail', args=[self.reserved_hall.pk])
        )

        self.assertEqual(response.status_code, 404)
