from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product
from .forms import ProductForm


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    ordering = ['name']

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'product/list.html'
    context_object_name = 'product'

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/confirm_delete.html'
    success_url = reverse_lazy('products:list')