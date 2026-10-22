
from django.urls import reverse_lazy
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


# Mostrar el detalle de una categoría
class CategoriesDetailView(DetailView):
    model = Category
    template_name = 'categories/detail.html'
    context_object_name = 'category'


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


# Eliminar una categoría
class CategoriesDeleteView(DeleteView):
    model = Category
    template_name = 'categories/confirm_delete.html'
    success_url = reverse_lazy('categories:list')
