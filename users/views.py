from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import User


from .forms import UserModelForm, UserUpdateForm
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


class TodosUsuariosView(BasicConfiguration, ListView):
    model = User
    template_name = 'users/index.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

class AgregarUsuario(BasicConfiguration, CreateView):
    form_class = UserModelForm
    template_name = 'users/add_user_form.html'
    success_url = reverse_lazy('users:allUsers')


    
class UserUpdate(BasicConfiguration, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/update.html'
    context_object_name = 'user'
    success_url = reverse_lazy('users:allUsers')
    permission_required = [
        'users.add_user',
        'users.view_user',
        'users.change_user',
        'users.delete_user',
    ]


