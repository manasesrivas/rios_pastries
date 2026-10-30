from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Venue


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


class VenueDetailView(PermissionsClient, DetailView):
    model = Venue
    template_name = 'venues/detail.html'
    context_object_name = 'venue'


class VenueCreateView(AdminPermission, CreateView):
    model = Venue
    fields = ['name', 'imagen', 'address', 'descripcion', 'capacity', 'status']
    template_name = 'venues/form.html'
    success_url = reverse_lazy('venues:list')


class VenueUpdateView(AdminPermission, UpdateView):
    model = Venue
    fields = ['name', 'imagen', 'address', 'descripcion', 'capacity', 'status']
    template_name = 'venues/form.html'
    success_url = reverse_lazy('venues:list')
    context_object_name = 'venue'


class VenueDeleteView(AdminPermission, DeleteView):
    model = Venue
    template_name = 'venues/confirm_delete.html'
    success_url = reverse_lazy('venues:list')

