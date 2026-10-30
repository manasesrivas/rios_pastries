from django.db import models

class StateVenue(models.TextChoices):
    DISPONIBLE = 'DISPONIBLE', 'Disponible'
    RESERVADO = 'RESERVADO', 'Reservado'

class Venue(models.Model):
    name = models.CharField(max_length=100)
    imagen = models.URLField(max_length=500, blank=True, null=True)
    address = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    capacity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=StateVenue.choices,
        default=StateVenue.DISPONIBLE
    )

    def __str__(self):
        return f"{self.nombre} - {self.get_status_display()}"
