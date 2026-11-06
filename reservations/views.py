from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ReservationForm
from .models import EstadoReservacion, Reservation


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


class ReservationFormMixin:
    form_class = ReservationForm
    template_name = 'reservations/form.html'
    success_url = reverse_lazy('reservations:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['can_manage'] = can_manage_reservations(self.request.user)
        return kwargs


class ReservationCreateView(ReservationFormMixin, PermissionsClient, CreateView):
    model = Reservation


class ReservationUpdateView(ReservationFormMixin, AdminPermission, UpdateView):
    model = Reservation
    context_object_name = 'reservation'

    def get_queryset(self):
        # Una reservación eliminada ya no se puede editar.
        return Reservation.objects.select_related('cliente', 'sala').exclude(
            estado=EstadoReservacion.ELIMINADA
        )


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