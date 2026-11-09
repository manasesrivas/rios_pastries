from django import forms
from django.forms import inlineformset_factory
from .models import Reservation, ReservationItem

INPUT_CLASSES = (
    'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-gray-600 dark:bg-gray-900 dark:text-white'
)

ReservationItemFormSet = inlineformset_factory(
    Reservation,
    ReservationItem,
    fields=['product', 'cantidad'],
    extra=1,
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': INPUT_CLASSES}),
        'cantidad': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'min': 1}),
    },
)