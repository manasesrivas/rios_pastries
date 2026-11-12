from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import CustomTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # Agrega el refresh token a la lista negra

            return Response({"detail": "Sesión cerrada correctamente."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Token inválido o no proporcionado."}, status=status.HTTP_400_BAD_REQUEST)




class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# users/api_view.py  (agrega a lo que ya tienes)
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle

from .models import EmailOTP
from .otp import create_and_send_otp
from users.serializers import RegisterSerializer, VerifyOTPSerializer, ResendOTPSerializer

User = get_user_model()
MAX_ATTEMPTS = 5

class OTPThrottle(AnonRateThrottle):
    rate = "5/min"

class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        create_and_send_otp(user)
        return Response(
            {"detail": "Usuario creado. Te enviamos un código a tu correo.", "email": user.email},
            status=status.HTTP_201_CREATED,
        )

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        invalid = Response({"error": "Código inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if not user:
            return invalid

        otp = user.otps.filter(is_used=False).first()
        if not otp or otp.expires_at < timezone.now() or otp.attempts >= MAX_ATTEMPTS:
            return invalid

        if not check_password(code, otp.code_hash):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            return invalid

        otp.is_used = True
        otp.save(update_fields=["is_used"])
        user.is_active = True
        user.save(update_fields=["is_active"])

        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=False).first()
        if user:
            create_and_send_otp(user)
        # Misma respuesta exista o no, para no revelar qué correos están registrados
        return Response({"detail": "Si el correo existe, enviamos un nuevo código."})