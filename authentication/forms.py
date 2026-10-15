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
