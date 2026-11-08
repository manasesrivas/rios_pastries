from django.shortcuts import render, HttpResponseRedirect, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import LoginForm, UserRegisterForm
from django.views import View
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy

from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect
from django.utils.encoding import force_str

from .emails import send_verification_email

from django import forms
class ResendVerificationForm(forms.Form):
    email = forms.EmailField(label='Correo Electronico')

class ResendVerificationView(FormView):
    form_class = ResendVerificationForm
    template_name = 'authentication/resend_verification.html'
    success_url = reverse_lazy('authentication:verification_email')

    def form_valid(self, form):
        User = get_user_model()
        email = form.cleaned_data['email']

        user = User.objects.filter(
            email__iexact=email, is_active=False
        )

        if user:
            send_verification_email(self.request, user)
        return redirect(self.success_url)

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Tu correo fue verificacdo correctamente')
            return redirect('users:home')
        messages.error(request, 'El enlace de verificacion es invaliddo')
        return redirect('authentication:register')

class UsersCreateView(CreateView):
    form_class = UserRegisterForm
    template_name = 'authentication/register.html'
    success_url = reverse_lazy('authentication:verification_sent')

    def form_valid(self, form):
        self.object = form.save()
        send_verification_email(self.request, self.object)
        return redirect(self.success_url)


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

            