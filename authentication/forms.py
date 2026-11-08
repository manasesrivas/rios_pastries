from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

TAILWIND_INPUT_CLASSES = (
    'w-full rounded-lg border border-gray-300 bg-white px-4 py-3 '
    'text-gray-900 shadow-sm outline-none transition '
    'placeholder:text-gray-400 focus:border-indigo-500 '
    'focus:ring-2 focus:ring-indigo-200'
)


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        max_length=100,
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Introduce un correo electrónico válido.'
        },
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'nombre@ejemplo.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Tu contraseña',
            'autocomplete': 'current-password',
        }),
        error_messages={
            'required': 'La contraseña es obligatoria.'
        }
    )



from users.models import User


class UserRegisterForm(UserCreationForm):
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
            'required': True,
            'class': TAILWIND_INPUT_CLASSES,
            'pattern':"[0-9]{4}-[0-9]{4}"
            })
        )
    class Meta:
        model = User
        fields = [
            'nombres',
            'apellidos',
            'email',
            'telefono'
        ]

        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'email': 'Correo electrónico',
            'telefono': 'Telefono'
        }

        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Ingresa tus nombres',
                'autocomplete': 'given-name',
            }),
            'apellidos': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Ingresa tus apellidos',
                'autocomplete': 'family-name',
            }),
            'email': forms.EmailInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, placeholder in (
            ('password1', 'Crea una contraseña'),
            ('password2', 'Confirma tu contraseña'),
        ):
            self.fields[field_name].widget.attrs.update({
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': placeholder,
            })


    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        user.save()

        if commit:
            grupo = Group.objects.get(name="Cliente")
            print(f'grupo ===============================================>: {grupo}')
            user.groups.add(grupo)

        return user
