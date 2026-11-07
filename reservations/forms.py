from datetime import date
from users.models import User
from django import forms

from .models import EstadoReservacion, Reservation

INPUT_CLASSES = (
    'block w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 '
    'text-sm text-gray-900 shadow-sm placeholder:text-gray-400 '
    'focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 '
    'dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder:text-gray-500'
)


class ReservationCreateForm(forms.ModelForm):
    """
    - El cliente no se elige: lo asigna la vista (usuario autenticado).
    - La sala se elige con tarjetas (RadioSelect), no con un select.
    - El estado solo existe al editar; al crear siempre es PENDIENTE.
    """

    class Meta:
        model = Reservation
        fields = ['fecha_evento', 'cantidad_personas', 'estado']

        labels = {
            'fecha_evento': 'Fecha del evento',
            'cantidad_personas': 'Cantidad de personas',
            'estado': 'Estado',
        }

        widgets = {
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

    def __init__(self, *args, sala=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sala = sala  # el UpdateView no la pasa, entonces queda en None

        if self.instance.pk:
            # Eliminar se hace desde la vista de borrado, no desde aquí.
            self.fields['estado'].choices = [
                choice for choice in EstadoReservacion.choices
                if choice[0] != EstadoReservacion.ELIMINADA
            ]
        else:
            del self.fields['estado']

    def clean_fecha_evento(self):
        fecha = self.cleaned_data['fecha_evento']
        if 'fecha_evento' in self.changed_data and fecha < date.today():
            raise forms.ValidationError(
                'La fecha del evento no puede estar en el pasado.'
            )
        return fecha

    def clean(self):
        cleaned_data = super().clean()

        sala = self.sala or (self.instance.sala if self.instance.sala_id else None)
        fecha = cleaned_data.get('fecha_evento')
        estado = cleaned_data.get('estado') or self.instance.estado
        inactivas = [EstadoReservacion.CANCELADA, EstadoReservacion.ELIMINADA]

        if sala and fecha and estado not in inactivas:
            ocupada = Reservation.objects.filter(
                sala=sala, fecha_evento=fecha
            ).exclude(estado__in=inactivas)
            if self.instance.pk:
                ocupada = ocupada.exclude(pk=self.instance.pk)
            if ocupada.exists():
                raise forms.ValidationError(
                    'Esta sala ya tiene una reservación activa para esa fecha.'
                )
        return cleaned_data


class ReservationUpdateForm(forms.ModelForm):
    """
    - El cliente no se elige: lo asigna la vista (usuario autenticado).
    - La sala se elige con tarjetas (RadioSelect), no con un select.
    - El estado solo existe al editar; al crear siempre es PENDIENTE.
    """
 
    class Meta:
        model = Reservation
        fields = ['sala', 'fecha_evento', 'cantidad_personas', 'estado']
 
        labels = {
            'sala': 'Sala',
            'fecha_evento': 'Fecha del evento',
            'cantidad_personas': 'Cantidad de personas',
            'estado': 'Estado',
        }
 
        widgets = {
            'sala': forms.RadioSelect(),
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

    @staticmethod
    def cliente_disponibles():
        return User.objects.filter(
            estado=User.Estado.ACTIVO,
            groups__name="Cliente"
        )
    
 
    def __init__(self, *args, sala=None, cliente=None, can_manage=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.sala = sala
        self.can_manage = can_manage
        self.cliente = cliente
        self.clientes = None

        if can_manage:
            self.clientes = self.cliente_disponibles().order_by('nombres', 'apellidos')
            self.fields['cliente_email'] = forms.CharField(
                label='Cliente',
                widget=forms.TextInput(attrs={
                    'class': INPUT_CLASSES,
                    'list': 'clientes-list',
                    'placeholder': 'Busca por nombre o correo…',
                    'autocomplete': 'off',
                }),
            )
            if self.cliente is not None:
                self.fields['cliente_email'].initial = self.cliente.email

        if self.instance.pk:
            # Eliminar se hace desde la vista de borrado, no desde aquí.
            self.fields['estado'].choices = [
                choice for choice in EstadoReservacion.choices
                if choice[0] != EstadoReservacion.ELIMINADA
            ]
        else:
            del self.fields['estado']
 
    def clean_fecha_evento(self):
        fecha = self.cleaned_data['fecha_evento']
        if 'fecha_evento' in self.changed_data and fecha < date.today():
            raise forms.ValidationError(
                'La fecha del evento no puede estar en el pasado.'
            )
        return fecha

    def clean_cliente_email(self):
        valor = self.cleaned_data['cliente_email'].strip()
        cliente = self.cliente_disponibles().filter(
            email__iexact=valor
        ).first()
        if cliente is None: raise forms.ValidationError('Selecciona un cliente')
        self.cliente = cliente
        return valor

    def clean(self):
        cleaned_data = super().clean()
 
        # Al crear, el estado no está en el formulario y Django omite la
        # restricción condicional del modelo, así que se valida aquí.
        if not self.instance.pk:
            sala = cleaned_data.get('sala')
            fecha = cleaned_data.get('fecha_evento')
            if sala and fecha:
                ocupada = Reservation.objects.filter(
                    sala=sala, fecha_evento=fecha
                ).exclude(estado__in=[
                    EstadoReservacion.CANCELADA,
                    EstadoReservacion.ELIMINADA,
                ])
                if ocupada.exists():
                    raise forms.ValidationError(
                        'Esta sala ya tiene una reservación activa '
                        'para esa fecha.'
                    )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.can_manage and self.cliente is not None:
            instance.cliente = self.cliente
        if commit:
            instance.save()
        return instance