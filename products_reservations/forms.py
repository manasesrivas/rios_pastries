from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Reservation, ReservationItem
from products.models import Product

INPUT_CLASSES = (
    'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-gray-600 dark:bg-gray-900 dark:text-white'
)

# Queryset con solo productos activos (no eliminados).
# Product.objects usa ActiveProductManager que filtra status=ACTIVO
# y además que la categoría del producto también esté activa.
_active_products = Product.objects.all()


class ReservationItemForm(forms.ModelForm):
    """Form individual de item que filtra productos eliminados en el select."""

    class Meta:
        model = ReservationItem
        fields = ['product', 'cantidad']
        widgets = {
            'product': forms.Select(attrs={'class': INPUT_CLASSES}),
            'cantidad': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = _active_products


ReservationItemFormSet = inlineformset_factory(
    Reservation,
    ReservationItem,
    form=ReservationItemForm,
    extra=1,
    can_delete=True,
)