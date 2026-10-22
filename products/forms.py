from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'image',
            'description',
            'price',
            'category',
            'available',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto',
            }),
            'image': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL de la imagen',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto',
                'rows': 4,
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }