import logging
from smtplib import SMTPException

from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.contrib.auth.views import PasswordChangeView

from .models import User
from authentication.emails import send_verification_email


from .forms import UserModelForm, UserProfileForm, UserUpdateForm
DIR = 'users/'
logger = logging.getLogger(__name__)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from orders.models import Order
from reservations.models import Reservation
from products.models import Product
from users.models import User

@login_required
def dashboard_view(request):
    user = request.user
    context = {}
    
    # Comprobar si el usuario es staff/admin o pertenece a grupos administrativos
    is_admin = user.is_staff or user.groups.filter(name__in=['Administrador', 'Recepcionista']).exists()
    context['is_admin'] = is_admin

    if is_admin:
        # --- MÉTRICAS Y DATOS DE ADMINISTRADOR ---
        context['total_orders'] = Order.objects.count()
        context['pending_orders'] = Order.objects.filter(status__iexact='pendiente').count()
        context['total_revenue'] = Order.objects.aggregate(total=Sum('total'))['total'] or 0
        context['total_reservations'] = Reservation.objects.count()
        context['pending_reservations'] = Reservation.objects.filter(estado='pendiente').count()
        
        # Listas recientes para la tabla operativa
        context['recent_orders'] = Order.objects.select_related('user').order_by('-id')[:5]
        context['recent_reservations'] = Reservation.objects.select_related('cliente', 'sala').order_by('-fecha_evento')[:5]
    else:
        # --- MÉTRICAS Y DATOS DEL CLIENTE ---
        user_orders = Order.objects.filter(user=user)
        user_reservations = Reservation.objects.filter(cliente=user)
        
        context['my_orders_count'] = user_orders.count()
        context['my_active_orders'] = user_orders.exclude(status__iexact='entregado').count()
        context['my_reservations_count'] = user_reservations.count()
        
        # Listas propias del cliente
        context['my_orders'] = user_orders.select_related('user').order_by('-id')[:5]
        context['my_reservations'] = user_reservations.select_related('sala').order_by('-fecha_evento')[:5]

    return render(request, 'dashboard.html', context)


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actor = self.request.user
        context['can_resend_verification'] = (
            (actor.is_superuser or actor.groups.filter(name='Administrador').exists())
            and self.object.estado == User.Estado.ACTIVO
            and not self.object.is_active
        )
        return context


class UserResendVerificationView(BasicConfiguration, DetailView):
    model = User
    http_method_names = ['post']

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not request.user.is_superuser
            and not request.user.groups.filter(name='Administrador').exists()
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        target = self.get_object(
            queryset=self.get_queryset().filter(
                estado=User.Estado.ACTIVO,
                is_active=False,
            ),
        )
        try:
            sent = send_verification_email(request, target)
        except (SMTPException, OSError):
            logger.exception('Error al reenviar el correo de verificación del usuario %s', target.pk)
            messages.error(request, 'No se pudo enviar el correo de verificación.')
        else:
            if sent:
                messages.success(request, 'Se envió el correo de verificación.')
            else:
                logger.error('No se envió el correo de verificación del usuario %s', target.pk)
                messages.error(request, 'No se pudo enviar el correo de verificación.')
        return HttpResponseRedirect(reverse('users:detail', args=[target.pk]))


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
        print(pk)
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