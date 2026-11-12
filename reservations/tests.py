from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.db import IntegrityError, connection
from django.http import QueryDict
from django.test import SimpleTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from categories.models import Category
from halls.models import Hall
from products.models import Product, StatusProduct
from products_reservations.models import ReservationItem
from venues.models import Venue
from reservations.views import ReservationCreateView

from .models import EstadoReservacion, Reservation
from .serializers import ReservationSerializer, active_reservations


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
        self.category = Category.objects.create(name='Pasteles')
        self.product = Product.objects.create(
            name='Pastel', description='Pastel', price='12.50', category=self.category,
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
                'total_productos': '0.00',
                'items': [],
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
                'items': [{'product_id': self.product.pk, 'quantity': 1}],
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
                'items': [{'product_id': self.product.pk, 'quantity': 1}],
            },
            format='json',
        )
        capacity_response = self.client.post(
            self.create_url,
            {
                'fecha_evento': (fecha_ocupada + timedelta(days=1)).isoformat(),
                'cantidad_personas': 101,
                'sala': self.hall.pk,
                'items': [{'product_id': self.product.pk, 'quantity': 1}],
            },
            format='json',
        )

        self.assertEqual(occupied_response.status_code, 400)
        self.assertIn('fecha_evento', occupied_response.data)
        self.assertEqual(capacity_response.status_code, 400)
        self.assertIn('cantidad_personas', capacity_response.data)

    def test_create_at_collection_consolidates_items_and_uses_database_price(self):
        response = self.client.post(
            self.url,
            {
                'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
                'cantidad_personas': 50,
                'sala': self.hall.pk,
                'cliente': self.other_user.pk,
                'estado': EstadoReservacion.CANCELADA,
                'items': [
                    {'product_id': self.product.pk, 'quantity': 2, 'price': '0.01'},
                    {'product_id': self.product.pk, 'quantity': 3},
                ],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['cliente'], self.client_user.pk)
        self.assertEqual(response.data['estado'], EstadoReservacion.CONFIRMADA)
        self.assertEqual(response.data['hallName'], self.hall.name)
        self.assertEqual(response.data['venueName'], self.venue.name)
        self.assertEqual(response.data['venueAdress'], self.venue.address)
        self.assertIsNone(response.data['hall'])
        self.assertIsNone(response.data['venue'])
        self.assertEqual(response.data['total_productos'], '62.50')
        self.assertEqual(response.data['items'], [{
            'product': self.product.pk, 'name': 'Pastel', 'quantity': 5,
            'price': '12.50', 'subtotal': '62.50',
        }])
        self.assertEqual(ReservationItem.objects.filter(reservation_id=response.data['id']).count(), 1)

    def test_validation_collects_reservation_and_product_errors(self):
        self.product.available = False
        self.product.save(update_fields=['available'])
        second = Product.objects.create(
            name='Mesa extra', description='Mesa', price='5.00',
            category=self.category, available=False,
        )
        response = self.client.post(self.url, {
            'fecha_evento': (timezone.localdate() - timedelta(days=1)).isoformat(),
            'cantidad_personas': 101,
            'sala': self.hall.pk,
            'items': [
                {'product_id': self.product.pk, 'quantity': 1},
                {'product_id': second.pk, 'quantity': 1},
                {'product_id': 999999, 'quantity': 1},
            ],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('fecha_evento', response.data)
        self.assertIn('cantidad_personas', response.data)
        self.assertEqual(response.json()['items'], [
            {'product_id': self.product.pk, 'name': 'Pastel',
             'error': 'El producto "Pastel" no está disponible actualmente.'},
            {'product_id': second.pk, 'name': 'Mesa extra',
             'error': 'El producto "Mesa extra" no está disponible actualmente.'},
            {'product_id': 999999, 'name': None,
             'error': 'El producto no existe o fue eliminado.'},
        ])
        self.assertEqual(ReservationItem.objects.count(), 0)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_invalid_date_and_unavailable_product_are_reported_together(self):
        self.product.available = False
        self.product.save(update_fields=['available'])
        response = self.client.post(self.url, {
            'fecha_evento': 'fecha inválida',
            'cantidad_personas': 1, 'sala': self.hall.pk,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('fecha_evento', response.data)
        self.assertEqual(response.json()['items'][0]['product_id'], self.product.pk)

    def test_validation_collects_invalid_hall_and_unavailable_product(self):
        self.product.available = False
        self.product.save(update_fields=['available'])
        response = self.client.post(self.url, {
            'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
            'cantidad_personas': 1, 'sala': 999999,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('sala', response.data)
        self.assertEqual(response.data['items'][0]['product_id'], self.product.pk)

    def test_deleted_product_is_reported_as_missing(self):
        self.product.status = StatusProduct.ELIMINADO
        self.product.save(update_fields=['status'])
        response = self.client.post(self.url, {
            'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
            'cantidad_personas': 1, 'sala': self.hall.pk,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['items'][0]['error'], 'El producto no existe o fue eliminado.')

    def test_product_lookup_is_batched(self):
        second = Product.objects.create(
            name='Mesa', description='Mesa', price='5.00', category=self.category,
        )
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(self.url, {
                'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
                'cantidad_personas': 1, 'sala': self.hall.pk,
                'items': [
                    {'product_id': self.product.pk, 'quantity': 1},
                    {'product_id': second.pk, 'quantity': 2},
                ],
            }, format='json')
        self.assertEqual(response.status_code, 201)
        product_queries = [
            query for query in queries.captured_queries
            if 'FROM "products_product"' in query['sql']
        ]
        self.assertEqual(len(product_queries), 1)

    @override_settings(RESERVATIONS_REQUIRE_PRODUCTS=True)
    def test_items_required_and_quantity_positive(self):
        body = {
            'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
            'cantidad_personas': 1, 'sala': self.hall.pk,
        }
        for items in (None, [], [{'product_id': self.product.pk, 'quantity': 0}]):
            data = dict(body)
            if items is not None:
                data['items'] = items
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertIn('items', response.data)

    def test_products_are_optional_by_default(self):
        body = {
            'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
            'cantidad_personas': 1, 'sala': self.hall.pk,
        }
        for items in (None, []):
            data = dict(body)
            if items is not None:
                data['items'] = items
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['items'], [])
            self.assertEqual(response.data['total_productos'], '0.00')
            body['fecha_evento'] = (timezone.localdate() + timedelta(days=31)).isoformat()

    def test_partial_serializer_uses_instance_and_excludes_itself(self):
        reservation = Reservation.objects.create(
            cliente=self.client_user,
            fecha_evento=timezone.localdate() + timedelta(days=40),
            cantidad_personas=5, sala=self.hall,
        )
        serializer = ReservationSerializer(reservation, data={'cantidad_personas': 10}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer = ReservationSerializer(data={}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_cancelled_reservation_does_not_block_creation(self):
        date = timezone.localdate() + timedelta(days=30)
        Reservation.objects.create(
            cliente=self.other_user, fecha_evento=date, cantidad_personas=1,
            sala=self.hall, estado=EstadoReservacion.CANCELADA,
        )
        response = self.client.post(self.url, {
            'fecha_evento': date.isoformat(), 'cantidad_personas': 1,
            'sala': self.hall.pk,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_item_integrity_error_rolls_back_reservation(self):
        with patch('reservations.serializers.ReservationItem.objects.bulk_create',
                   side_effect=IntegrityError('error de escritura')):
            with self.assertRaises(IntegrityError):
                self.client.post(self.url, {
                    'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
                    'cantidad_personas': 1, 'sala': self.hall.pk,
                    'items': [{'product_id': self.product.pk, 'quantity': 1}],
                }, format='json')
        self.assertEqual(Reservation.objects.count(), 1)

    def test_unique_constraint_race_returns_field_error(self):
        date = timezone.localdate() + timedelta(days=30)
        Reservation.objects.create(
            cliente=self.other_user, fecha_evento=date, cantidad_personas=1, sala=self.hall,
        )
        no_conflict = Mock()
        no_conflict.exists.return_value = False
        existing = active_reservations(self.hall, date)
        with patch(
            'reservations.serializers.active_reservations',
            side_effect=[no_conflict, no_conflict, existing],
        ):
            response = self.client.post(self.url, {
                'fecha_evento': date.isoformat(), 'cantidad_personas': 1,
                'sala': self.hall.pk,
                'items': [{'product_id': self.product.pk, 'quantity': 1}],
            }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['fecha_evento'], [
            'Esta sala ya tiene una reservación activa para esa fecha.',
        ])
        self.assertEqual(ReservationItem.objects.count(), 0)

    def test_capacity_is_rechecked_after_locking_hall(self):
        updated_hall = Hall.objects.get(pk=self.hall.pk)
        updated_hall.capacity = 1
        with patch('reservations.serializers.Hall.objects.select_for_update') as select:
            select.return_value.filter.return_value.first.return_value = updated_hall
            response = self.client.post(self.url, {
                'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
                'cantidad_personas': 2, 'sala': self.hall.pk,
                'items': [{'product_id': self.product.pk, 'quantity': 1}],
            }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('cantidad_personas', response.data)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_create_requires_jwt_and_add_permission(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(self.url, {}, format='json').status_code, 401)
        self.client.force_authenticate(user=self.other_user)
        self.assertEqual(self.client.post(self.url, {}, format='json').status_code, 403)

    def test_create_accepts_jwt_bearer_token(self):
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {AccessToken.for_user(self.client_user)}')
        response = self.client.post(self.url, {
            'fecha_evento': (timezone.localdate() + timedelta(days=30)).isoformat(),
            'cantidad_personas': 1, 'sala': self.hall.pk,
            'items': [{'product_id': self.product.pk, 'quantity': 1}],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['cliente'], self.client_user.pk)


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
