from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Order
from .forms import OrderForm


class PermissionsClient(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'orders.view_order'
    raise_exception = True


class AdminPermission(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [
        'orders.view_order',
        'orders.add_order',
        'orders.change_order',
        'orders.delete_order',
    ]
    raise_exception = True


class OrderListView(PermissionsClient, ListView):
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']


class OrderDetailView(PermissionsClient, DetailView):
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'


class OrderCreateView(AdminPermission, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/form.html'
    success_url = reverse_lazy('orders:list')


class OrderUpdateView(AdminPermission, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/form.html'
    success_url = reverse_lazy('orders:list')


class OrderDeleteView(AdminPermission, DeleteView):
    model = Order
    template_name = 'orders/confirm_delete.html'
    success_url = reverse_lazy('orders:list')