from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ReservationCreateForm, ReservationUpdateForm
from .models import EstadoReservacion, Reservation

from products.models import Product
from products_reservations.models import ReservationItem
from halls.models import Hall
from django.shortcuts import get_object_or_404

from django.db import IntegrityError, transaction
from products_reservations.forms import ReservationItemFormSet

from .services import enviar_comprobante_email

def can_manage_reservations(user):
    """Superusuario, staff, Administrador o Cajero ven y gestionan todo."""
    return (
        user.is_superuser
        or user.is_staff
        or user.groups.filter(name__in=['Administrador', 'Cajero']).exists()
    )


class PermissionsClient(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [
        'reservations.view_reservation',
        'reservations.add_reservation',
    ]
    raise_exception = True


class AdminPermission(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [
        'reservations.view_reservation',
        'reservations.add_reservation',
        'reservations.change_reservation',
        'reservations.delete_reservation',
    ]
    raise_exception = True


class ReservationQuerysetMixin:
    """Administrador/Cajero ven todas; el Cliente solo las suyas."""

    def get_queryset(self):
        queryset = Reservation.objects.select_related('cliente', 'sala')
        if not can_manage_reservations(self.request.user):
            queryset = queryset.filter(cliente=self.request.user)
        return queryset


class ReservationListView(ReservationQuerysetMixin, PermissionsClient, ListView):
    model = Reservation
    template_name = 'reservations/list.html'
    context_object_name = 'reservations'

    def get_selected_estado(self):
        estado = self.request.GET.get('estado')
        if estado in EstadoReservacion.values:
            return estado
        return None

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-fecha_evento', '-pk')
        estado = self.get_selected_estado()
        if estado:
            return queryset.filter(estado=estado)
        # Sin filtro, las eliminadas no se muestran.
        return queryset.exclude(estado=EstadoReservacion.ELIMINADA)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estado_choices'] = EstadoReservacion.choices
        context['selected_estado'] = self.get_selected_estado()
        return context


class ReservationDetailView(ReservationQuerysetMixin, PermissionsClient, DetailView):
    model = Reservation
    template_name = 'reservations/detail.html'
    context_object_name = 'reservation'

    def get_queryset(self):
        return Reservation.objects.select_related('cliente', 'sala__venue').prefetch_related('items__product')






class ReservationCreateView(PermissionsClient, CreateView):
    model = Reservation
    form_class = ReservationCreateForm
    template_name = 'reservations/form.html'
    success_url = reverse_lazy('reservations:list')

    def get_queryset(self):
        # Una reservación eliminada ya no se puede editar.
        return Reservation.objects.select_related('cliente', 'sala').exclude(
            estado=EstadoReservacion.ELIMINADA
        )
    def hall(self):
        hall_pk = self.kwargs.get('pk')
        if hall_pk is None:
            return None
        return get_object_or_404(Hall, pk=hall_pk)

    def get_initial(self):
        initial = super().get_initial()
        hall = self.hall()
        if hall is not None:
            initial['sala'] = hall
        return initial

    def form_valid(self, form):
        manager = can_manage_reservations(self.request.user)
        formset = self.get_formset() if manager else None
        if formset is not None and not formset.is_valid():
            return self.form_invalid(form)

        cart_items = self.get_cart_items(form)
        if cart_items is None:
            return self.form_invalid(form)

        if not can_manage_reservations(self.request.user):
            form.instance.cliente = self.request.user
        hall = self.hall()
        if hall is not None:
            form.instance.sala = hall
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                if formset is not None:
                    formset.instance = self.object
                    for item in formset.save(commit=False):
                        item.precio_unitario = item.product.price
                        item.save()
                    for item in formset.deleted_objects:
                        item.delete()

                for product, quantity in cart_items:
                    ReservationItem.objects.create(
                        reservation=self.object,
                        product=product,
                        cantidad=quantity,
                        precio_unitario=product.price,
                    )
                transaction.on_commit(lambda: enviar_comprobante_email(self.object))

        except IntegrityError:
            # Respaldo: dos personas guardando a la vez
            form.add_error(None, 'Esta sala ya tiene una reservación activa para esa fecha.')
            return self.form_invalid(form)

        return response

    def get_cart_items(self, form):
        choice = self.request.POST.get('reservation_products', 'solo')
        if choice == 'solo':
            return []
        if choice != 'carrito':
            form.add_error(None, 'Selecciona si deseas agregar los productos del carrito.')
            return None

        product_ids = self.request.POST.getlist('cart_product_id')
        quantities = self.request.POST.getlist('cart_quantity')
        if not product_ids or len(product_ids) != len(quantities):
            form.add_error(
                None,
                'No se encontraron productos válidos en el carrito. '
                'Elige solo la reservación o vuelve a intentarlo.',
            )
            return None

        quantities_by_product = {}
        products_by_id = {}
        for product_id_value, quantity_value in zip(product_ids, quantities):
            try:
                product_id = forms.IntegerField(min_value=1).clean(product_id_value)
                quantity = forms.IntegerField(min_value=1).clean(quantity_value)
            except ValidationError:
                form.add_error(None, 'El carrito contiene productos o cantidades inválidas.')
                return None

            product = Product.objects.filter(pk=product_id).first()
            if product is None or not product.available:
                form.add_error(
                    None,
                    'Uno o más productos del carrito ya no están disponibles.',
                )
                return None

            products_by_id[product.pk] = product
            quantities_by_product[product.pk] = (
                quantities_by_product.get(product.pk, 0) + quantity
            )

        return [
            (product, quantities_by_product[product_id])
            for product_id, product in products_by_id.items()
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['sala'] = self.hall()
        # kwargs['cliente'] = self.request.user
        kwargs['can_manage'] = can_manage_reservations(self.request.user)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hall'] = self.hall()
        context['formset'] = self.get_formset()
        return context

    def get_formset(self):
        if not hasattr(self, '_formset'):
            data = self.request.POST if self.request.method == 'POST' else None
            self._formset = ReservationItemFormSet(data, instance=self.object)
        return self._formset
    
    


class ReservationUpdateView(AdminPermission, UpdateView):
    model = Reservation
    context_object_name = 'reservation'
    form_class = ReservationUpdateForm
    template_name = 'reservations/update.html'
    success_url = reverse_lazy('reservations:list')
    
    def get_queryset(self):
        # Una reservación eliminada ya no se puede editar.
        return Reservation.objects.select_related('cliente', 'sala').exclude(
            estado=EstadoReservacion.ELIMINADA
        )
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['sala'] = self.object.sala
        kwargs['cliente'] = self.object.cliente
        kwargs['can_manage'] = can_manage_reservations(self.request.user)
        return kwargs
    
    def form_valid(self, form):
        reservation = form.instance

        # 1. ¿Hay otra reservación activa para esa sala y esa fecha?
        if reservation.estado in (EstadoReservacion.PENDIENTE, EstadoReservacion.CONFIRMADA):
            hay_choque = Reservation.objects.filter(
                sala=reservation.sala,
                fecha_evento=reservation.fecha_evento,
                estado__in=[EstadoReservacion.PENDIENTE, EstadoReservacion.CONFIRMADA],
            ).exclude(pk=reservation.pk).exists()

            if hay_choque:
                form.add_error(None, 'Esta sala ya tiene una reservación activa para esa fecha.')
                return self.form_invalid(form)

        formset = self.get_formset()
        if not formset.is_valid():
            return self.form_invalid(form)

        try:
            with transaction.atomic():   # NUEVO: todo se guarda o nada
                response = super().form_valid(form)   # guarda la reservación

                # NUEVO: guardar los items
                for item in formset.save(commit=False):
                    if item.pk is None:   # item nuevo
                        item.precio_unitario = item.product.price
                    item.save()
                for item in formset.deleted_objects:
                    item.delete()
        except IntegrityError:
            form.add_error(None, 'Esta sala ya tiene una reservación activa para esa fecha.')
            return self.form_invalid(form)

        return response

    def get_formset(self):
        if not hasattr(self, '_formset'):
            data = self.request.POST if self.request.method == 'POST' else None
            self._formset = ReservationItemFormSet(data, instance=self.object)
        return self._formset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = self.get_formset()
        return context




class ReservationDeleteView(AdminPermission, DeleteView):
    model = Reservation
    template_name = 'reservations/delete.html'
    context_object_name = 'reservation'
    success_url = reverse_lazy('reservations:list')

    def get_queryset(self):
        return Reservation.objects.select_related('cliente', 'sala').exclude(
            estado=EstadoReservacion.ELIMINADA
        )

    def form_valid(self, form):
        # Borrado lógico: la fila se conserva con estado ELIMINADA.
        self.object.estado = EstadoReservacion.ELIMINADA
        self.object.save(update_fields=['estado'])
        return HttpResponseRedirect(self.get_success_url())