from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import User


from .forms import UserModelForm
DIR = 'users/'

# Create your views here.
@login_required
def home(request): return render(request, 'index.html')




class TodosUsuariosView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/index.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

class AgregarUsuario(CreateView):
    form_class = UserModelForm
    template_name = 'users/add_user_form.html'
    success_url = reverse_lazy('users:allUsers')


    
class UserUpdate(UpdateView):
    model = User
    form_class = UserModelForm
    template_name = 'users/update.html'
    context_object_name = 'user'
    success_url = reverse_lazy('users:allUsers')

    # def get(self, request, *args, **kargs):
    #     return render(request, 'users/update.html', {'form': self.form_class})

