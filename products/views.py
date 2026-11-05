from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from orders.forms import OrderForm
from .models import Product
from .forms import ProductForm

class PermissionsClient(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'products.view_product'
    raise_exception = True

class AdminPermission(LoginRequiredMixin, PermissionRequiredMixin):
    raise_exception = True

class ProductListView(PermissionsClient, ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    ordering = ['name']

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     if self.request.user.groups.filter(name='Cliente').exists():
    #         queryset = queryset.filter(available=True)
    #     return queryset

class ProductDetailView(PermissionsClient, DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_form'] = OrderForm(max_quantity=self.object.stock)
        return context

class ProductCreateView(AdminPermission, CreateView):
    permission_required = 'products.add_product'
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    context_object_name = 'product'
    success_url = reverse_lazy('products:list')

class ProductUpdateView(AdminPermission, UpdateView):
    permission_required = 'products.change_product'
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    context_object_name = 'product'
    success_url = reverse_lazy('products:list')

class ProductDeleteView(AdminPermission, DeleteView):
    permission_required = 'products.delete_product'
    model = Product
    template_name = 'products/confirm_delete.html'
    context_object_name = 'product'
    success_url = reverse_lazy('products:list')
