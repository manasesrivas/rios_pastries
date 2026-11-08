from django import forms
from reservations.models import Reservation, EstadoReservacion
from .models import Order


class OrderForm(forms.Form):
    reservation = forms.ModelChoiceField(
        label='Reservación',
        queryset=Reservation.objects.none(),
        empty_label='Selecciona una reservación',
        widget=forms.Select(
            attrs={
                'class': (
                    'min-h-11 w-full rounded-lg border border-gray-300 '
                    'bg-white px-3 py-2 text-sm text-gray-900 shadow-sm '
                    'outline-none focus:border-indigo-500 focus:ring-2 '
                    'focus:ring-indigo-500/20 dark:border-gray-600 '
                    'dark:bg-gray-800 dark:text-white'
                ),
            }
        ),
    )
    quantity = forms.IntegerField(
        label='Cantidad',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                'id': 'quantity',
                'class': (
                    'w-16 border-x border-gray-200 bg-white text-center '
                    'text-gray-900 outline-none focus-visible:z-10 '
                    'focus-visible:ring-2 focus-visible:ring-inset '
                    'focus-visible:ring-indigo-500 dark:border-gray-600 '
                    'dark:bg-gray-900 dark:text-white'
                ),
                'inputmode': 'numeric',
            }
        ),
    )
    metodo_pago = forms.ChoiceField(
        label='Método de pago',
        choices=[
            ('', 'Selecciona un método de pago'),
            *Order.MetodoPago.choices,
        ],
        widget=forms.Select(
            attrs={
                'class': (
                    'min-h-11 w-full rounded-lg border border-gray-300 '
                    'bg-white px-3 py-2 text-sm text-gray-900 shadow-sm '
                    'outline-none focus:border-indigo-500 focus:ring-2 '
                    'focus:ring-indigo-500/20 dark:border-gray-600 '
                    'dark:bg-gray-800 dark:text-white'
                ),
            }
        ),
    )
    tipo_entrega = forms.ChoiceField(
        label='Tipo de entrega',
        choices=[
            ('', 'Selecciona un tipo de entrega'),
            *Order.TipoEntrega.choices,
        ],
        widget=forms.Select(
            attrs={
                'class': (
                    'min-h-11 w-full rounded-lg border border-gray-300 '
                    'bg-white px-3 py-2 text-sm text-gray-900 shadow-sm '
                    'outline-none focus:border-indigo-500 focus:ring-2 '
                    'focus:ring-indigo-500/20 dark:border-gray-600 '
                    'dark:bg-gray-800 dark:text-white'
                ),
            }
        ),
    )

    def __init__(self, *args, max_quantity=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reservation'].queryset = Reservation.objects.filter(
            estado=EstadoReservacion.CONFIRMADA
        )
        '''
        Descomentar cuando se use para los items de reservacion
        '''
        # if max_quantity is not None:
        #     self.fields['quantity'].max_value = max_quantity
        #     self.fields['quantity'].widget.attrs['max'] = max_quantity
