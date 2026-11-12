from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import QueryDict
from django.test import SimpleTestCase
from django.utils import timezone
from django.urls import reverse

from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from halls.models import Hall
from venues.models import Venue
from reservations.views import ReservationCreateView

from .models import EstadoReservacion, Reservation


User = get_user_model()


class ReservationAPITests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email='reservation-api@example.com',
            password='SecurePass123!',
        )
        self.other_user = User.objects.create_user(
            email='other-reservation-api@example.com',
            password='SecurePass123!',
        )
        self.client_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='reservations',
                codename='view_reservation',
            ),
            Permission.objects.get(
                content_type__app_label='reservations',
                codename='add_reservation',
            ),
        )
        self.client.force_authenticate(user=self.client_user)

        self.venue = Venue.objects.create(
            name='Centro de eventos',
            address='San Salvador',
        )
        self.hall = Hall.objects.create(
            venue=self.venue,
            name='Salón principal',
            capacity=100,
            price='250.00',
        )
        self.reservation = Reservation.objects.create(
            cliente=self.client_user,
            fecha_evento='2026-11-15',
            cantidad_personas=50,
            sala=self.hall,
        )
        self.url = reverse('reservations_api:list')
        self.create_url = reverse('reservations_api:create')

    def test_list_serializes_model_fields_and_real_hall_and_venue_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0],
            {
                'id': self.reservation.pk,
                'cliente': self.client_user.pk,
                'fecha_evento': '2026-11-15',
                'cantidad_personas': 50,
                'sala': self.hall.pk,
                'estado': EstadoReservacion.CONFIRMADA,
                'hallName': 'Salón principal',
                'venueName': 'Centro de eventos',
                'venueAdress': 'San Salvador',
                'hall': None,
                'venue': None,
            },
        )

    def test_client_only_sees_own_non_deleted_reservations(self):
        Reservation.objects.create(
            cliente=self.other_user,
            fecha_evento='2026-11-16',
            cantidad_personas=20,
            sala=self.hall,
        )
        Reservation.objects.create(
            cliente=self.client_user,
            fecha_evento='2026-11-17',
            cantidad_personas=30,
            sala=self.hall,
            estado=EstadoReservacion.ELIMINADA,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [self.reservation.pk])

    def test_administrator_can_see_all_non_deleted_reservations(self):
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        self.client_user.groups.add(admin_group)
        other_reservation = Reservation.objects.create(
            cliente=self.other_user,
            fecha_evento='2026-11-16',
            cantidad_personas=20,
            sala=self.hall,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item['id'] for item in response.data},
            {self.reservation.pk, other_reservation.pk},
        )

    def test_list_requires_authentication_and_view_permission(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

        no_permission_user = User.objects.create_user(
            email='without-permission@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=no_permission_user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_create_assigns_authenticated_client_and_model_default_state(self):
        fecha_evento = timezone.localdate() + timedelta(days=10)
        response = self.client.post(
            self.create_url,
            {
                'fecha_evento': fecha_evento.isoformat(),
                'cantidad_personas': 40,
                'sala': self.hall.pk,
                'cliente': self.other_user.pk,
                'estado': EstadoReservacion.CANCELADA,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        reservation = Reservation.objects.get(pk=response.data['id'])
        self.assertEqual(reservation.cliente, self.client_user)
        self.assertEqual(reservation.estado, EstadoReservacion.CONFIRMADA)

    def test_create_rejects_occupied_hall_and_over_capacity(self):
        fecha_ocupada = timezone.localdate() + timedelta(days=10)
        Reservation.objects.create(
            cliente=self.other_user,
            fecha_evento=fecha_ocupada,
            cantidad_personas=20,
            sala=self.hall,
        )
        occupied_response = self.client.post(
            self.create_url,
            {
                'fecha_evento': fecha_ocupada.isoformat(),
                'cantidad_personas': 40,
                'sala': self.hall.pk,
            },
            format='json',
        )
        capacity_response = self.client.post(
            self.create_url,
            {
                'fecha_evento': (fecha_ocupada + timedelta(days=1)).isoformat(),
                'cantidad_personas': 101,
                'sala': self.hall.pk,
            },
            format='json',
        )

        self.assertEqual(occupied_response.status_code, 400)
        self.assertIn('fecha_evento', occupied_response.data)
        self.assertEqual(capacity_response.status_code, 400)
        self.assertIn('cantidad_personas', capacity_response.data)


class ReservationCreateUrlTests(SimpleTestCase):
    def test_create_url_without_hall_id(self):
        self.assertEqual(reverse('reservations:create'), '/reservations/create/')

    def test_create_url_with_hall_id(self):
        self.assertEqual(
            reverse('reservations:create', args=[7]),
            '/reservations/create/7/',
        )


class ReservationCartSelectionTests(SimpleTestCase):
    def setUp(self):
        self.view = ReservationCreateView()
        self.form = Mock()

    def test_only_reservation_does_not_read_cart(self):
        self.view.request = SimpleNamespace(POST=QueryDict('reservation_products=solo'))

        with patch('reservations.views.Product.objects.filter') as product_filter:
            self.assertEqual(self.view.get_cart_items(self.form), [])

        product_filter.assert_not_called()

    def test_cart_products_are_validated_and_duplicate_products_aggregated(self):
        self.view.request = SimpleNamespace(POST=QueryDict(
            'reservation_products=carrito'
            '&cart_product_id=7&cart_quantity=2'
            '&cart_product_id=7&cart_quantity=3'
        ))
        product = SimpleNamespace(pk=7, available=True)

        with patch('reservations.views.Product.objects.filter') as product_filter:
            product_filter.return_value.first.return_value = product
            items = self.view.get_cart_items(self.form)

        self.assertEqual(items, [(product, 5)])

    def test_selected_empty_cart_returns_a_form_error(self):
        self.view.request = SimpleNamespace(POST=QueryDict('reservation_products=carrito'))

        self.assertIsNone(self.view.get_cart_items(self.form))
        self.form.add_error.assert_called_once()

    def test_invalid_cart_quantity_returns_a_form_error(self):
        self.view.request = SimpleNamespace(POST=QueryDict(
            'reservation_products=carrito&cart_product_id=7&cart_quantity=0'
        ))

        with patch('reservations.views.Product.objects.filter') as product_filter:
            self.assertIsNone(self.view.get_cart_items(self.form))

        product_filter.assert_not_called()
        self.form.add_error.assert_called_once()
