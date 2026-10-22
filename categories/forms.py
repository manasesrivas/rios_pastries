from django import forms
from .models import Category

class CategoriesForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']