from django.db import models


from django.db import models
from users.models import User


class Pedido(models.Model):
    cliente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="pedidos"
    )

    productos = models.ManyToManyField(
        "productos.Product",
        through="DetallePedido",
        related_name="pedidos"
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    fecha = models.DateField(
        auto_now_add=True
    )

    hora = models.TimeField(
        auto_now_add=True
    )

    direccion = models.TextField(
        blank=True,
        null=True
    )


    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente}"
