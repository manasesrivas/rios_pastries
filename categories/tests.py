from django.test import TestCase
from django.urls import reverse

from products.forms import ProductForm

from .models import Category


class CategoryStatusTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Pasteles')

    def test_new_categories_are_active(self):
        self.assertEqual(self.category.status, Category.Status.ACTIVO)

    def test_list_only_shows_active_categories(self):
        deleted_category = Category.objects.create(
            name='Categoría eliminada',
            status=Category.Status.ELIMINADO,
        )

        response = self.client.get(reverse('categories:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)
        self.assertNotContains(response, deleted_category.name)

    def test_delete_marks_category_as_deleted_without_removing_it(self):
        confirmation = self.client.get(
            reverse('categories:delete', args=[self.category.pk])
        )
        self.assertEqual(confirmation.status_code, 200)

        response = self.client.post(
            reverse('categories:delete', args=[self.category.pk])
        )

        self.assertRedirects(response, reverse('categories:list'))
        self.category.refresh_from_db()
        self.assertEqual(self.category.status, Category.Status.ELIMINADO)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        self.assertNotContains(self.client.get(reverse('categories:list')), self.category.name)

    def test_deleted_category_cannot_be_opened_for_detail_or_update(self):
        self.category.status = Category.Status.ELIMINADO
        self.category.save(update_fields=['status'])

        self.assertEqual(
            self.client.get(
                reverse('categories:detail', args=[self.category.pk])
            ).status_code,
            404,
        )

    def test_product_form_only_offers_active_categories(self):
        deleted_category = Category.objects.create(
            name='Bebidas',
            status=Category.Status.ELIMINADO,
        )

        form_categories = ProductForm().fields['category'].queryset

        self.assertIn(self.category, form_categories)
        self.assertNotIn(deleted_category, form_categories)
        self.assertEqual(
            self.client.get(
                reverse('categories:update', args=[self.category.pk])
            ).status_code,
            404,
        )
