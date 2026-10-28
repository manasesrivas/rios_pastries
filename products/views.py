from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Product
from .forms import ProductForm

class PermissionsClient(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'products.view_product'
    raise_exception = True

class AdminPermission(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [
        'products.view_product',
        'products.add_product',
        'products.change_product',
        'products.delete_product',
    ]

    raise_exception = True

class ProductListView(PermissionsClient, ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    ordering = ['name']

class ProductDetailView(PermissionsClient, DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

class ProductCreateView(AdminPermission, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

class ProductUpdateView(AdminPermission, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

class ProductDeleteView(AdminPermission, DeleteView):
    model = Product
    template_name = 'products/confirm_delete.html'
    success_url = reverse_lazy('products:list')