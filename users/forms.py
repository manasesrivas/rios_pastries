from django import forms
from .models import Roles
from django.core.validators import RegexValidator

class UserForm(forms.Form):

    nombres = forms.CharField()
    apellidos = forms.CharField()

    email = forms.EmailField(label='email')

    telefono = forms.CharField(
        label="Teléfono",
        max_length=9,
        validators=[
            RegexValidator(
                regex=r'^\d{9}$',
                message="Ingresa un teléfono de exactamente 9 dígitos."
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': '123456789',
            'type': 'tel',
        })
    )
    
    rol = forms.ModelChoiceField(
        queryset=Roles.objects.all(),
        label='elije un rol',
        widget=forms.Select(
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput()
    )

from .models import User

class UserModelForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nombres', 'apellidos', 'email', 'rol']