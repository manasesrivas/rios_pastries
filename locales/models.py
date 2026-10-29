from django.db import models


class Sala(models.Model):
    ESTADO_DISPONIBLE = 'disponible'
    ESTADO_RESERVADO = 'reservado'

    ESTADOS_CHOICES = [
        (ESTADO_DISPONIBLE, 'Disponible'),
        (ESTADO_RESERVADO, 'Reservado'),
    ]

    nombre = models.CharField(max_length=100)
    imagen = models.URLField(max_length=500, blank=True, null=True)
    direccion = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    capacidad = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CHOICES,
        default=ESTADO_DISPONIBLE
    )

    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'

    def __str__(self):
        return f"{self.nombre} - {self.get_estado_display()}"
