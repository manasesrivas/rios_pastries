from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required

from django.contrib.auth.views import PasswordChangeView

from .models import User


from .forms import UserModelForm, UserProfileForm, UserUpdateForm
DIR = 'users/'

# Create your views here.
@login_required
def home(request): return render(request, 'index.html')


class BasicConfiguration(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [
        'users.add_user',
        'users.view_user',
        'users.change_user',
        'users.delete_user',
    ]
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not request.user.is_superuser
            and request.user.groups.filter(name='Cliente').exists()
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True).filter(
                estado=User.Estado.ACTIVO,
            )
        return queryset


class UserListView(BasicConfiguration, ListView):
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return super().get_queryset().exclude(pk=self.request.user.pk)


class UserCreateView(BasicConfiguration, CreateView):
    form_class = UserModelForm
    template_name = 'users/form.html'
    success_url = reverse_lazy('users:list')

class UserDetailView(BasicConfiguration, DetailView):
    model = User
    template_name = 'users/detail.html'
    context_object_name = 'user'


class UserUpdateView(BasicConfiguration, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/update.html'
    context_object_name = 'user'
    success_url = reverse_lazy('users:list')

    def get_queryset(self):
        return super().get_queryset().filter(estado=User.Estado.ACTIVO)

    def get_success_url(self):
        return reverse('users:detail', kwargs={'pk': self.object.pk})


class UserDeleteView(BasicConfiguration, DeleteView):
    model = User
    template_name = 'users/delete.html'
    context_object_name = 'user'
    success_url = reverse_lazy('users:list')

    def get_queryset(self):
        return super().get_queryset().filter(estado=User.Estado.ACTIVO)

    def get_object(self, queryset=None):
        user = super().get_object(queryset)
        if user.pk == self.request.user.pk:
            raise PermissionDenied
        return user

    def form_valid(self, form):
        self.object.estado = User.Estado.ELIMINADO
        self.object.is_active = False
        self.object.save(update_fields=['estado', 'is_active'])
        return HttpResponseRedirect(self.get_success_url())


class UserRestoreView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        user = get_object_or_404(
            User,
            pk=pk,
            estado=User.Estado.ELIMINADO,
        )
        user.estado = User.Estado.ACTIVO
        user.is_active = True
        user.save(update_fields=['estado', 'is_active'])
        return HttpResponseRedirect(reverse('users:detail', kwargs={'pk': pk}))


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:profile')