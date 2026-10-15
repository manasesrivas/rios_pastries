from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        max_length=100,
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Introduce un correo eletrónico válido.'
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        error_messages={
            'required': 'La contraseña es obligatória'
        }
    )


from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from users.models import User


class UserRegisterForm(forms.ModelForm):

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

    

    class Meta:
        model = User
        fields = [
            'nombres',
            'apellidos',
            'email',
            'password',
        ]

        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'email': 'Correo electrónico',
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
            apellidos=self.cleaned_data['apellidos'],
        )
        if commit: user.save()
        return user

