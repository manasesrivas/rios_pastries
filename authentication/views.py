from django.shortcuts import render, HttpResponseRedirect, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, UserRegisterForm
from django.views import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
# Create your views here.

class UsersCreateView(CreateView):
    form_class = UserRegisterForm
    template_name = 'authentication/register.html'
    success_url = reverse_lazy('users:home')
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)

        return response


class LoginView(View): 
    form_class = LoginForm
    template_name = 'authentication/login.html'
    def get(self, request, *args, **kargs):
        return render(request, self.template_name, {'form': self.form_class})

    def post(self, request, *args, **kargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(
                request=request,
                email=email,
                password=password
            )
            if user is not None:
                login(request, user)
                return redirect('users:home')

        form.add_error(None, 'Correo electrónico o contraseña incorrectos.')

        return render(
            request,
            self.template_name,
            {'form': form}
        )

def logout_view(request):
    logout(request)
    return redirect('authentication:login')

            