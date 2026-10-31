from django import forms

from .models import Hall


class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ['venue', 'name', 'image', 'capacity', 'price', 'status']
        widgets = {
            'image': forms.URLInput(attrs={'placeholder': 'URL de la imagen'}),
            'capacity': forms.NumberInput(attrs={'min': 1}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }
