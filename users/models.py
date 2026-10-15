from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from roles.models import Roles


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un email')

        if 'rol' not in extra_fields or extra_fields['rol'] is None:
            extra_fields['rol'] = Roles.objects.get(rol='Cliente')

        email = self.normalize_email(email)
        
        user = self.model(
            email = email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        administrador = Roles.objects.get(rol='Administrador')
        return self.create_user(
            email=email,
            password=password,
            rol=administrador,
            **extra_fields
        )

class User(AbstractBaseUser):
    nombres = models.CharField(null=True, blank=True, max_length=100)
    apellidos = models.CharField(null=True, blank=True, max_length=100)

    telefono = models.CharField(max_length=9)
    email = models.EmailField(
        unique=True,
    )
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True)
    objects = UserManager()
    
    USERNAME_FIELD = 'email'


