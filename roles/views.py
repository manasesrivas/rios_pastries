from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import *
from .forms import *

# Create your views here.
class RolesView(LoginRequiredMixin, View):
    form_class = RolForm
    template_name = 'rol/form.html'
    # initial = {'key': 'value'}
    def get(self, request, *args, **kargs):
        return render(request, self.template_name, {'form': self.form_class})

    def post(self, request, *args, **kargs):
        form = self.form_class(request.POST)
        if(form.is_valid()):
            rol = Roles(rol=form.cleaned_data['rol'])
            rol.save()
            return redirect('roles:allRoles')

class TodosRolesView(LoginRequiredMixin, ListView):
    model = Roles
    template_name = 'rol/index.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)
