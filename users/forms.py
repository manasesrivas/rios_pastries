from django import forms
from .models import Roles
from django.core.validators import RegexValidator


from .models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

class UserModelForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña',
            'autocomplete': 'new-password',
        }),
        error_messages={
            'required': 'La contraseña es obligatoria.',
        },
    )

    telefono = forms.CharField(
        label="Teléfono",
        max_length=9,
        validators=[
            RegexValidator(
                regex=r'^\d{4}-\d{4}$',
                message="Ingresa un teléfono de exactamente 9 dígitos."
            )
        ],
        widget=forms.NumberInput(attrs={
        'type': 'tel',
        'placeholder': '1234-1234',
        'maxlength': '9',
        'pattern': r'[0-9]{4}-[0-9]{4}',
        'required': True
        })
    )
    

    class Meta:
        model = User
        fields = [
            'nombres',
            'apellidos',
            'telefono',
            'email',
            'password',
            'rol'
        ]

        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'email': 'Correo electrónico',
            'rol': 'elije un rol'
        }

        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tus nombres',
                'autocomplete': 'given-name',
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tus apellidos',
                'autocomplete': 'family-name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@correo.com',
                'autocomplete': 'email',
            }),
            'rol': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            )
        }

        error_messages = {
            'nombres': {
                'required': 'Los nombres son obligatorios.',
            },
            'apellidos': {
                'required': 'Los apellidos son obligatorios.',
            },
            'email': {
                'required': 'El correo electrónico es obligatorio.',
                'invalid': 'Introduce un correo electrónico válido.',
                'unique': 'Este correo electrónico ya está registrado.',
            },
        }


    def clean_password(self):
        password = self.cleaned_data.get('password')

        password_validation.validate_password(
            password,
            user=self.instance,
        )

        return password

    def save(self, commit=True):
        if not commit:
            raise ValueError(
                'Este formulario requiere guardar el usuario.'
            )

        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            nombres=self.cleaned_data['nombres'],
            telefono=self.cleaned_data['telefono'],
            apellidos=self.cleaned_data['apellidos'],
            rol=self.cleaned_data['rol']
        )
        if commit: user.save()
        return user