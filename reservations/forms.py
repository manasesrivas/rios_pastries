from datetime import date

from django import forms
from django.db.models import Q

from users.models import User

from .models import EstadoReservacion, Reservation

INPUT_CLASSES = (
    'block w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 '
    'text-sm text-gray-900 shadow-sm placeholder:text-gray-400 '
    'focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 '
    'disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-500 '
    'dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder:text-gray-500 '
    'dark:disabled:bg-gray-700 dark:disabled:text-gray-400'
)


class ReservationForm(forms.ModelForm):
    """
    Si recibe `user` y este no es de gestión (Cliente), el cliente queda fijo
    en ese usuario y el estado en PENDIENTE. Los campos se deshabilitan en
    lugar de quitarlos para que la restricción única siga validándose.
    """

    class Meta:
        model = Reservation
        fields = [
            'cliente',
            'sala',
            'fecha_evento',
            'cantidad_personas',
            'estado',
        ]

        labels = {
            'cliente': 'Cliente',
            'sala': 'Sala',
            'fecha_evento': 'Fecha del evento',
            'cantidad_personas': 'Cantidad de personas',
            'estado': 'Estado',
        }

        widgets = {
            'cliente': forms.Select(attrs={'class': INPUT_CLASSES}),
            'sala': forms.Select(attrs={'class': INPUT_CLASSES}),
            'fecha_evento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': INPUT_CLASSES, 'type': 'date'},
            ),
            'cantidad_personas': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'min': '1',
                'placeholder': 'Ej. 25',
            }),
            'estado': forms.Select(attrs={'class': INPUT_CLASSES}),
        }

    def __init__(self, *args, user=None, can_manage=True, **kwargs):
        super().__init__(*args, **kwargs)

        # Eliminar se hace desde la vista de borrado, no desde el formulario.
        self.fields['estado'].choices = [
            choice for choice in EstadoReservacion.choices
            if choice[0] != EstadoReservacion.ELIMINADA
        ]

        if can_manage:
            # Solo usuarios activos (más el cliente actual al editar).
            filtro = Q(estado=User.Estado.ACTIVO)
            if self.instance.pk:
                filtro |= Q(pk=self.instance.cliente_id)
            self.fields['cliente'].queryset = User.objects.filter(filtro)
        elif user is not None:
            # El cliente no ve ni elige a otros usuarios.
            self.fields['cliente'].queryset = User.objects.filter(pk=user.pk)
            self.fields['cliente'].disabled = True
            self.initial['cliente'] = user.pk
            self.fields['estado'].disabled = True
            self.initial['estado'] = EstadoReservacion.PENDIENTE

    def clean_fecha_evento(self):
        fecha = self.cleaned_data['fecha_evento']
        if 'fecha_evento' in self.changed_data and fecha < date.today():
            raise forms.ValidationError(
                'La fecha del evento no puede estar en el pasado.'
            )
        return fecha