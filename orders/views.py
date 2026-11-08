
from django.db import transaction
from django.db.models import Sum
from django import forms
from django.core.exceptions import ValidationError
from products.models import Product
from detail_orders.models import DetailOrder, Status
from django.urls import reverse_lazy
from django.http import HttpResponseBadRequest
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
    View
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .forms import OrderForm
from .models import Order

from .utils import is_store_open


from .services import publish_order_update

from django.contrib import messages


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
        queryset = Order.objects.all()
        # Si es superusuario, staff o pertenece al grupo Administrador o Cajero, ve todos los pedidos
        if not (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name__in=['Administrador', 'Cajero']).exists()
        ):
            # Si es Cliente (o cualquier otro usuario), solo ve sus propios pedidos
            queryset = queryset.filter(user=user)
        return queryset.annotate(product_quantity=Sum('order__quantity'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['can_receive_order_notifications'] = (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name__in=['Administrador', 'Cajero']).exists()
        )
        return context


class OrderDetailView(PermissionsClient, DetailView):
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.Estado.choices
        return context

    def get_queryset(self):
        user = self.request.user
        # Si es superusuario, staff o pertenece al grupo Administrador o Cajero, puede ver el detalle de cualquier pedido
        if user.is_superuser or user.is_staff or user.groups.filter(name__in=['Administrador', 'Cajero']).exists():
            return Order.objects.all()
        # Si es Cliente, solo puede ver el detalle de sus propios pedidos
        return Order.objects.filter(user=user)


class OrderStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'
    fields = ['status']
    permission_required = 'orders.change_order'
    raise_exception = True
    http_method_names = ['post']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.Estado.choices
        return context

    def get_success_url(self):
        return reverse('orders:detail', kwargs={'pk': self.object.pk})



class OrderCreateView(PermissionsClient, View):
    model = Order
    success_url = reverse_lazy('orders:list')

    def post(self, request):
        # 1. Validación de Horario Comercial (9:00 AM - 7:00 PM)
        if not is_store_open():
            return HttpResponseBadRequest(
                'El horario para realizar pedidos en línea es de 9:00 a. m. a 7:00 p. m. '
                'Actualmente el negocio se encuentra CERRADO para pedidos.'
            )

        # 2. Validar los datos generales de la orden (método de pago, tipo de entrega, dirección)
        form = OrderForm(request.POST)
        if not form.is_valid():
            product_ids = request.POST.getlist('product_id')
            if len(product_ids) == 1:
                product = get_object_or_404(Product, pk=product_ids[0])
                return render(
                    request,
                    'products/detail.html',
                    {'product': product, 'order_form': form},
                )
            return HttpResponseBadRequest(form.errors.as_text())

        # 3. Procesar y validar productos y cantidades recibidos
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')

        if not product_ids or len(product_ids) != len(quantities):
            return HttpResponseBadRequest(
                'Envía al menos un producto y una cantidad por cada producto.'
            )

        products_by_id = {}
        quantities_by_id = {}

        for product_id, quantity_value in zip(product_ids, quantities):
            product = get_object_or_404(Product, pk=product_id)
            
            # Verificar disponibilidad individual del producto
            if not product.available:
                return HttpResponseBadRequest(
                    f'El producto "{product.name}" no está disponible actualmente.'
                )

            try:
                quantity = forms.IntegerField(min_value=1).clean(quantity_value)
            except ValidationError as error:
                return HttpResponseBadRequest('; '.join(error.messages))

            products_by_id[product.pk] = product
            quantities_by_id[product.pk] = (
                quantities_by_id.get(product.pk, 0) + quantity
            )

        if not products_by_id:
            return HttpResponseBadRequest('No se recibieron productos válidos.')

        # 4. Guardado atómico en base de datos y envío de notificación
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                subtotal=0,
                total=0,
                direccion=form.cleaned_data.get('direccion', ''),
                metodo_pago=form.cleaned_data['metodo_pago'],
                tipo_entrega=form.cleaned_data['tipo_entrega'],
            )

            status_pendiente, _ = Status.objects.get_or_create(
                name=Status.PENDIENTE
            )

            total = 0
            product_names = []
            notification_products = []
            product_quantity = 0

            for product_id, product in products_by_id.items():
                quantity = quantities_by_id[product_id]
                subtotal_item = product.price * quantity

                DetailOrder.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    subtotal=subtotal_item,
                    status=status_pendiente
                )

                total += subtotal_item
                product_names.append(product.name)
                notification_products.append({
                    'name': product.name,
                    'quantity': quantity,
                    'unit_price': str(product.price),
                    'subtotal': str(subtotal_item),
                })
                product_quantity += quantity

            order.subtotal = total
            order.total = total
            order.save()

            # Preparación de payload para publicación en WebSocket / Tareas en segundo plano
            notification_data = {
                'order_id': order.pk,
                'product_name': ', '.join(product_names),
                'products': notification_products,
                'order_date': order.fecha.strftime('%d/%m/%Y'),
                'order_time': order.hora.strftime('%H:%M'),
                'customer_name': (
                    f'{getattr(order.user, "nombres", "") or order.user.email} '
                    f'{getattr(order.user, "apellidos", "") or ""}'
                ).strip(),
                'product_quantity': product_quantity,
                'payment_method': order.get_metodo_pago_display(),
                'delivery_type': order.get_tipo_entrega_display(),
                'total': str(order.total),
                'status': order.status,
            }

            transaction.on_commit(
                lambda data=notification_data: publish_order_update(**data)
            )
            messages.success(request, 'ORDER_CREATED_SUCCESS')

        return redirect(self.success_url)
    


class OrderUpdateView(AdminPermission, UpdateView):
    model = Order
    template_name = 'orders/form.html'
    success_url = reverse_lazy('orders:list')
    fields = ['direccion', 'metodo_pago', 'tipo_entrega']


class OrderDeleteView(AdminPermission, DeleteView):
    model = Order
    template_name = 'orders/confirm_delete.html'
    success_url = reverse_lazy('orders:list')


class OrderCheckoutView(LoginRequiredMixin, View):
    template_name = 'orders/checkout.html'

    def get(self, request):
        return render(request, self.template_name, {'order_form': OrderForm()})
