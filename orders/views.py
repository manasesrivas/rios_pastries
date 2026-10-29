from products.models import Product
from detail_orders.models import DetailOrder, Status
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
    View
)
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Order

class PermissionsClient(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = ['orders.view_order', 'orders.add_order']
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

    def get_queryset(self):
        user = self.request.user
        # Si es superusuario, staff o pertenece al grupo Administrador o Cajero, ve todos los pedidos
        if user.is_superuser or user.is_staff or user.groups.filter(name__in=['Administrador', 'Cajero']).exists():
            return Order.objects.all()
        # Si es Cliente (o cualquier otro usuario), solo ve sus propios pedidos
        return Order.objects.filter(user=user)


class OrderDetailView(PermissionsClient, DetailView):
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        user = self.request.user
        # Si es superusuario, staff o pertenece al grupo Administrador o Cajero, puede ver el detalle de cualquier pedido
        if user.is_superuser or user.is_staff or user.groups.filter(name__in=['Administrador', 'Cajero']).exists():
            return Order.objects.all()
        # Si es Cliente, solo puede ver el detalle de sus propios pedidos
        return Order.objects.filter(user=user)


class OrderCreateView(PermissionsClient, View):
    model = Order
    success_url = reverse_lazy('orders:list')

    def post(self, request):
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, pk=product_id)
        user = request.user
        quantity = int(request.POST.get('quantity', 1))

        # 1. Obtener la última orden del usuario o crear una nueva si no existe
        order = Order.objects.filter(user=user).last()
        if not order:
            order = Order.objects.create(
                user=user,
                subtotal=0,
                total=0,
                direccion=''
            )

        # 2. Si el producto ya está en el detalle, actualizar quantity y subtotal
        detail = DetailOrder.objects.filter(order=order, product=product).first()
        if detail:
            detail.quantity += quantity
            detail.subtotal = detail.quantity * detail.price
            detail.save()
        else:
            # Si no existe, crear el detalle con estado inicial 'pendiente'
            status_pendiente, _ = Status.objects.get_or_create(name=Status.PENDIENTE)
            DetailOrder.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
                subtotal=product.price * quantity,
                status=status_pendiente
            )

        # 3. Actualizar el subtotal y total de la orden con todos sus detalles
        detalles = DetailOrder.objects.filter(order=order)
        nuevo_total = sum(d.subtotal for d in detalles)
        order.subtotal = nuevo_total
        order.total = nuevo_total
        order.save()

        return redirect(self.success_url)

    


class OrderUpdateView(AdminPermission, View):
    model = Order
    template_name = 'orders/form.html'
    success_url = reverse_lazy('orders:list')


class OrderDeleteView(AdminPermission, DeleteView):
    model = Order
    template_name = 'orders/confirm_delete.html'
    success_url = reverse_lazy('orders:list')

class ProductsOrderListView(ListView):
    model = Product
    template_name = 'orders/user/list.html'
    context_object_name = 'products'