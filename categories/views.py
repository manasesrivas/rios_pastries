
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Category
from .forms import CategoriesForm


# Listar todas las categorías
class CategoriesListView(ListView):
    model = Category
    template_name = 'categories/list.html'
    context_object_name = 'categories'
    ordering = ['name']

    def get_queryset(self):
        return super().get_queryset().filter(status=Category.Status.ACTIVO)


# Mostrar el detalle de una categoría
class CategoriesDetailView(DetailView):
    model = Category
    template_name = 'categories/detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return super().get_queryset().filter(status=Category.Status.ACTIVO)


# Crear una categoría
class CategoriesCreateView(CreateView):
    model = Category
    form_class = CategoriesForm
    template_name = 'categories/form.html'
    success_url = reverse_lazy('categories:list')


# Actualizar una categoría
class CategoriesUpdateView(UpdateView):
    model = Category
    form_class = CategoriesForm
    template_name = 'categories/form.html'
    success_url = reverse_lazy('categories:list')

    def get_queryset(self):
        return super().get_queryset().filter(status=Category.Status.ACTIVO)


# Marcar una categoría como eliminada
class CategoriesDeleteView(DeleteView):
    model = Category
    template_name = 'categories/confirm_delete.html'
    success_url = reverse_lazy('categories:list')

    def get_queryset(self):
        return super().get_queryset().filter(status=Category.Status.ACTIVO)

    def form_valid(self, form):
        self.object.status = Category.Status.ELIMINADO
        self.object.save(update_fields=['status'])
        return HttpResponseRedirect(self.get_success_url())
