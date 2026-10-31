from django.db import models


class HallStatus(models.TextChoices):
    DISPONIBLE = 'DISPONIBLE', 'Disponible'
    RESERVADO = 'RESERVADO', 'Reservado'


class Hall(models.Model):
    venue = models.ForeignKey(
        'venues.Venue',
        on_delete=models.PROTECT,
        related_name='halls',
    )
    name = models.CharField(max_length=100)
    image = models.URLField(max_length=500, blank=True, null=True)
    capacity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=HallStatus.choices,
        default=HallStatus.DISPONIBLE,
    )

    def __str__(self):
        return self.name
