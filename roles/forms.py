from .models import Roles
from django import forms

class RolForm(forms.Form):
    rol = forms.CharField(label='rol', max_length=30)
