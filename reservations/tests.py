from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import QueryDict
from django.test import SimpleTestCase
from django.urls import reverse

from reservations.views import ReservationCreateView


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
