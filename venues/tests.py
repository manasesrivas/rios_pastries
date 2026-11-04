from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import StateVenue, Venue


class VenueViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(email='venue-admin@example.com')
        self.venue = Venue.objects.create(
            name='Salón Central',
            address='Avenida Principal 123',
            descripcion='Espacio para eventos.',
        )

    def grant_permissions(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label='venues',
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)
        self.client.force_login(self.user)

    def test_list_displays_venues_as_a_list(self):
        self.grant_permissions('view_venue')

        response = self.client.get(reverse('venues:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<ul')
        self.assertContains(response, 'Salón Central')
        self.assertContains(response, 'Avenida Principal 123')
        self.assertContains(response, reverse('venues:detail', args=[self.venue.pk]))
        self.assertNotContains(response, 'Activo')

    def test_list_only_displays_active_venues(self):
        deleted_venue = Venue.objects.create(
            name='Local eliminado',
            address='Otra dirección',
            status=StateVenue.ELIMINADO,
        )
        self.grant_permissions('view_venue')

        response = self.client.get(reverse('venues:list'))

        self.assertContains(response, 'Salón Central')
        self.assertNotContains(response, deleted_venue.name)

    def test_detail_displays_venue_information(self):
        self.grant_permissions('view_venue')

        response = self.client.get(
            reverse('venues:detail', args=[self.venue.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Salón Central')
        self.assertContains(response, 'Avenida Principal 123')
        self.assertContains(response, 'Espacio para eventos.')

    def test_delete_confirmation_displays_venue_and_does_not_delete_it(self):
        self.grant_permissions(
            'view_venue',
            'add_venue',
            'change_venue',
            'delete_venue',
        )

        response = self.client.get(
            reverse('venues:delete', args=[self.venue.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¿Eliminar Salón Central?')
        self.assertContains(response, 'Avenida Principal 123')
        self.assertContains(response, 'Sí, eliminar local')
        self.assertTrue(Venue.objects.filter(pk=self.venue.pk).exists())

    def test_delete_marks_venue_as_eliminated_instead_of_removing_it(self):
        self.grant_permissions(
            'view_venue',
            'add_venue',
            'change_venue',
            'delete_venue',
        )

        response = self.client.post(
            reverse('venues:delete', args=[self.venue.pk])
        )

        self.assertRedirects(response, reverse('venues:list'))
        self.venue.refresh_from_db()
        self.assertEqual(self.venue.status, StateVenue.ELIMINADO)
        self.assertTrue(Venue.objects.filter(pk=self.venue.pk).exists())

    def test_create_form_does_not_include_removed_image_field(self):
        self.grant_permissions(
            'view_venue',
            'add_venue',
            'change_venue',
            'delete_venue',
        )

        response = self.client.get(reverse('venues:create'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="imagen"')
