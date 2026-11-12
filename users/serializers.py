from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Ejecuta la validación por defecto para generar el access y refresh
        data = super().validate(attrs)

        first_group = self.user.groups.first()

        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'nombres': getattr(self.user, 'nombres', ''),
            'apellidos': getattr(self.user, 'apellidos', ''),
            'grupo': first_group.name if first_group else ''
        }

        return data



# users/serializers.py  (agrega a lo que ya tienes)
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(is_active=False, **validated_data)

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()