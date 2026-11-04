from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from venues.models import Venue

from .models import Hall, HallStatus


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
