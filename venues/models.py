from django.db import models

class StateVenue(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    ELIMINADO = 'eliminado', 'Eliminado'

class Venue(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=StateVenue.choices,
        default=StateVenue.ACTIVO,
    )

    def __str__(self):
        return f"{self.name}"
