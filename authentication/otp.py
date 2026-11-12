# users/otp.py
import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone
from .models import EmailOTP

OTP_TTL_MINUTES = 10

def create_and_send_otp(user):
    # Invalida códigos anteriores
    EmailOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    code = f"{secrets.randbelow(10**6):06d}"  # criptográficamente seguro
    EmailOTP.objects.create(
        user=user,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
    )
    send_mail(
        subject="Tu código de verificación",
        message=f"Tu código es {code}. Expira en {OTP_TTL_MINUTES} minutos.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )