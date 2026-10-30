from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Sala


class PermissionsClient(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'locales.view_sala'
    raise_exception = True


class AdminPermission(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [
        'locales.view_sala',
        'locales.add_sala',
        'locales.change_sala',
        'locales.delete_sala',
    ]
    raise_exception = True


class SalaListView(PermissionsClient, ListView):
    model = Sala
    template_name = 'locales/list.html'
    context_object_name = 'locales'
    ordering = ['nombre']


class SalaDetailView(PermissionsClient, DetailView):
    model = Sala
    template_name = 'locales/detail.html'
    context_object_name = 'local'


class SalaCreateView(AdminPermission, CreateView):
    model = Sala
    fields = ['nombre', 'imagen', 'direccion', 'descripcion', 'capacidad', 'estado']
    template_name = 'locales/form.html'
    success_url = reverse_lazy('locales:list')


class SalaUpdateView(AdminPermission, UpdateView):
    model = Sala
    fields = ['nombre', 'imagen', 'direccion', 'descripcion', 'capacidad', 'estado']
    template_name = 'locales/form.html'
    success_url = reverse_lazy('locales:list')
    context_object_name = 'local'


class SalaDeleteView(AdminPermission, DeleteView):
    model = Sala
    template_name = 'locales/confirm_delete.html'
    success_url = reverse_lazy('locales:list')


