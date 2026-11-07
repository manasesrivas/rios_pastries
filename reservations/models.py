from django.db import models
from django.db.models import Q
from halls.models import Hall
from users.models import User


class EstadoReservacion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    CONFIRMADA = 'CONFIRMADA', 'Confirmada'
    CANCELADA = 'CANCELADA', 'Cancelada'
    FINALIZDA = 'FINALIZADA' 'Finalizada'
    ELIMINADA = 'ELIMINADA', 'Eliminada'


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
                condition=~Q(estado__in=[
                    EstadoReservacion.CANCELADA,
                    EstadoReservacion.ELIMINADA,
                ]),
                name='unique_sala_fecha_evento',
                violation_error_message=(
                    'Esta sala ya tiene una reservación activa para esa fecha.'
                ),
            )
        ]

    def __str__(self):
        return f'Reservación #{self.pk} - {self.sala} ({self.fecha_evento})'