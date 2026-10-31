from django.db import models
from venues.models import Venue
from users.models import User

class EstadoReservacion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    CONFIRMADA = 'CONFIRMADA', 'Confirmada'
    CANCELADA = 'CANCELADA', 'Cancelada'

class Reservation(models.Model):
    cliente = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    fecha_evento = models.DateField()

    cantidad_personas = models.PositiveIntegerField()
    sala = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name='reservations'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoReservacion.choices,
        default=EstadoReservacion.PENDIENTE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['sala', 'fecha_evento'],
                name='unique_sala_fecha_evento'
            )
        ]