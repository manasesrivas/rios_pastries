from django.db import models
from django.db.models import Q
from halls.models import Hall
from users.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class EstadoReservacion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    CONFIRMADA = 'CONFIRMADA', 'Confirmada'
    CANCELADA = 'CANCELADA', 'Cancelada'
    FINALIZDA = 'FINALIZADA' 'Finalizada'
    ELIMINADA = 'ELIMINADA', 'Eliminada'


INACTIVE_RESERVATION_STATES = [
    EstadoReservacion.CANCELADA,
    EstadoReservacion.ELIMINADA,
]


class Reservation(models.Model):
    cliente = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    fecha_evento = models.DateField()

    cantidad_personas = models.PositiveIntegerField()
    sala = models.ForeignKey(
        Hall,
        on_delete=models.PROTECT,
        related_name='reservations'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoReservacion.choices,
        default=EstadoReservacion.CONFIRMADA
    )

    class Meta:
        constraints = [
            # Solo las reservaciones activas bloquean la sala en esa fecha.
            models.UniqueConstraint(
                fields=['sala', 'fecha_evento'],
                condition=~Q(estado__in=INACTIVE_RESERVATION_STATES),
                name='unique_sala_fecha_evento',
                violation_error_message=(
                    'Esta sala ya tiene una reservación activa para esa fecha.'
                ),
            )
        ]

    def __str__(self):
        return f'Reservación #{self.pk} - {self.sala} ({self.fecha_evento})'
    def clean(self):
        super().clean()
        if self.fecha_evento is None:
            return

        if self.fecha_evento < timezone.localdate():
            fecha_original = None
            if self.pk:
                fecha_original = (
                    Reservation.objects.filter(pk=self.pk)
                    .values_list('fecha_evento', flat=True)
                    .first()
                )
            # Solo bloquea si la fecha es nueva o la están cambiando a una pasada
            if fecha_original != self.fecha_evento:
                raise ValidationError({'fecha_evento': 'No puedes elegir una fecha pasada.'})

    @property
    def total_productos(self):
        return sum(item.subtotal for item in self.items.all())