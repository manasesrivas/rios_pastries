
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Categories
from .forms import CategoriesForm


# Listar todas las categorías
class CategoriesListView(ListView):
    model = Categories
    template_name = 'categories/list.html'
    context_object_name = 'categories'
    ordering = ['name']


# Mostrar el detalle de una categoría
class CategoriesDetailView(DetailView):
    model = Categories
    template_name = 'categories/detail.html'
    context_object_name = 'category'


# Crear una categoría
class CategoriesCreateView(CreateView):
    model = Categories
    form_class = CategoriesForm
    template_name = 'categories/form.html'
    success_url = reverse_lazy('categories:list')


# Actualizar una categoría
class CategoriesUpdateView(UpdateView):
    model = Categories
    form_class = CategoriesForm
    template_name = 'categories/form.html'
    success_url = reverse_lazy('categories:list')


# Eliminar una categoría
class CategoriesDeleteView(DeleteView):
    model = Categories
    template_name = 'categories/confirm_delete.html'
    success_url = reverse_lazy('categories:list')
