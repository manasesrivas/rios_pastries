from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import StateVenue, Venue


class PermissionsClient(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'venues.view_venue'
    raise_exception = True


class AdminPermission(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [
        'venues.view_venue',
        'venues.add_venue',
        'venues.change_venue',
        'venues.delete_venue',
    ]
    raise_exception = True


class VenueListView(PermissionsClient, ListView):
    model = Venue
    template_name = 'venues/list.html'
    context_object_name = 'venues'
    ordering = ['name']

    def get_queryset(self):
        return super().get_queryset().filter(status=StateVenue.ACTIVO)


class VenueDetailView(PermissionsClient, DetailView):
    model = Venue
    template_name = 'venues/detail.html'
    context_object_name = 'venue'

    def get_queryset(self):
        return super().get_queryset().filter(status=StateVenue.ACTIVO)


class VenueCreateView(AdminPermission, CreateView):
    model = Venue
    fields = ['name', 'address', 'descripcion']
    template_name = 'venues/form.html'
    success_url = reverse_lazy('venues:list')


class VenueUpdateView(AdminPermission, UpdateView):
    model = Venue
    fields = ['name', 'address', 'descripcion', 'status']
    template_name = 'venues/form.html'
    success_url = reverse_lazy('venues:list')
    context_object_name = 'venue'

    def get_queryset(self):
        return super().get_queryset().filter(status=StateVenue.ACTIVO)


class VenueDeleteView(AdminPermission, DeleteView):
    model = Venue
    template_name = 'venues/confirm_delete.html'
    success_url = reverse_lazy('venues:list')

    def get_queryset(self):
        return super().get_queryset().filter(status=StateVenue.ACTIVO)

    def form_valid(self, form):
        self.object.status = StateVenue.ELIMINADO
        self.object.save(update_fields=['status'])
        return HttpResponseRedirect(self.get_success_url())
