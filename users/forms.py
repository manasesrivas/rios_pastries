from django import forms
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.contrib.auth.forms import UserCreationForm


from .models import User
from django.contrib.auth import password_validation

# formulario para agregar usuarios desde el panel de administracion
class UserModelForm(UserCreationForm):

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
    
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Tipo de usuario",
        empty_label="Selecciona un grupo",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    class Meta:
        model = User
        fields = [
            'nombres',
            'apellidos',
            'telefono',
            'email',
        ]

        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'email': 'Correo electrónico',
            'tipo usuario': 'tipo Usuario'
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




    def save(self, commit=True):
        if not commit:
            raise ValueError(
                'Este formulario requiere guardar el usuario.'
            )
        user = super().save(commit=commit)

        if commit:
            grupo = self.cleaned_data['grupo']
            user.groups.add(grupo)
        return user

class UserUpdateForm(forms.ModelForm):

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
    
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Tipo de usuario",
        empty_label="Selecciona un grupo",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    class Meta:
        model = User
        fields = [
            'nombres',
            'apellidos',
            'telefono',
            'email',
        ]

        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'email': 'Correo electrónico',
            'tipo usuario': 'tipo Usuario'
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




    def save(self, commit=True):
        if not commit:
            raise ValueError(
                'Este formulario requiere guardar el usuario.'
            )
        user = super().save(commit=commit)

        if commit:
            grupo = self.cleaned_data['grupo']
            user.groups.add(grupo)
        return user
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['grupo'].initial = self.instance.groups.first()

    def save(self, commit=True):
        if not commit:
            raise ValueError(
                'Este formulario requiere guardar el usuario.'
            )
        user = super().save(commit=commit)

        if commit:
            grupo = self.cleaned_data['grupo']
            user.groups.add(grupo)
        return user