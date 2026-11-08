from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse('authentication:activate', kwargs={'uidb64': uid, 'token': token})
    activation_url = f"{request.scheme}://{get_current_site(request).domain}{path}"

    message = render_to_string('authentication/activation_email.txt', {
        'user': user,
        'activation_url': activation_url,
    })
    send_mail(
        subject='Verifica tu correo electrónico',
        message=message,
        from_email=None,
        recipient_list=[user.email],
    )