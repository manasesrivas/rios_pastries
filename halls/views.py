from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .models import Hall, HallStatus
from .forms import HallForm


class HallVisibilityMixin:
    def get_queryset(self):
        queryset = Hall.objects.select_related('venue')
        if not self.request.user.has_perm('halls.change_hall'):
            queryset = queryset.filter(status=HallStatus.DISPONIBLE)
        return queryset


class HallListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    HallVisibilityMixin,
    ListView,
):
    model = Hall
    template_name = 'halls/list.html'
    context_object_name = 'halls'
    permission_required = 'halls.view_hall'

    def get_queryset(self):
        return super().get_queryset().order_by('name')


class HallDetailView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    HallVisibilityMixin,
    DetailView,
):
    model = Hall
    template_name = 'halls/detail.html'
    context_object_name = 'hall'
    permission_required = 'halls.view_hall'


class HallCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Hall
    form_class = HallForm
    template_name = 'halls/form.html'
    success_url = reverse_lazy('halls:list')
    permission_required = 'halls.add_hall'


class HallUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Hall
    form_class = HallForm
    template_name = 'halls/form.html'
    success_url = reverse_lazy('halls:list')
    permission_required = 'halls.change_hall'


class HallDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Hall
    template_name = 'halls/confirm_delete.html'
    success_url = reverse_lazy('halls:list')
    permission_required = 'halls.delete_hall'
