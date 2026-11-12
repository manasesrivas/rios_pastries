from django.shortcuts import render, HttpResponseRedirect, HttpResponse, redirect
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from .forms import LoginForm, UserRegisterForm
from django.views import View
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.contrib.auth.views import PasswordResetView
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
        self.object.is_active = False
        self.object.save(update_fields=['is_active'])
        send_verification_email(self.request, self.object)
        return redirect(self.success_url)


class LoginView(View): 
    form_class = LoginForm
    template_name = 'authentication/login.html'
    def get(self, request, *args, **kargs):
        return render(request, self.template_name, {
            'form': self.form_class,
            'next': request.GET.get('next', ''),
        })

    def post(self, request, *args, **kargs):
        form = self.form_class(request.POST)
        next_url = request.POST.get('next', '')
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
                if url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect('users:home')

        form.add_error(None, 'Correo electrónico o contraseña incorrectos.')

        return render(
            request,
            self.template_name,
            {'form': form, 'next': next_url}
        )


@login_required
@require_GET
@never_cache
def apk_page(request):
    return render(request, 'authentication/apk_download.html', {
        'apk_available': settings.APK_FILE_PATH.is_file(),
    })


@login_required
@require_GET
@never_cache
def apk_download(request):
    try:
        apk_file = settings.APK_FILE_PATH.open('rb')
    except FileNotFoundError as error:
        raise Http404('El APK aún no está disponible.') from error
    return FileResponse(
        apk_file,
        as_attachment=True,
        filename='rios-pastries.apk',
        content_type='application/vnd.android.package-archive',
    )


def logout_view(request):
    logout(request)
    return redirect('authentication:login')


class AuthenticationResetPasswordView(PasswordResetView):
    template_name='password_reset/password_reset_form.html'
    email_template_name='password_reset/password_reset_email.txt'
    subject_template_name='password_reset/password_reset_subject.txt'
    success_url=reverse_lazy('authentication:password_reset_done')
