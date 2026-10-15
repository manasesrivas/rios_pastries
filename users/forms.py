from django import forms
from .models import Roles

class UserForm(forms.Form):

    nombres = forms.CharField()
    apellidos = forms.CharField()

    email = forms.EmailField(label='email')
    
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