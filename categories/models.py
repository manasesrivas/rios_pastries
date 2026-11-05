from django.db import models

class Category(models.Model):
    class Status(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        ELIMINADO = 'eliminado', 'Eliminado'

    name = models.CharField(unique=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVO,
    )

    def __str__(self):
        return self.name
