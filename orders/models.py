from django.db import models
from users.models import User


class Order(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ENTREGADO = 'entregado', 'Entregado'
        APARTADO = 'apartado', 'Apartado'
        CANCELADO = 'cancelado', 'Cancelado'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        TARJETA = 'tarjeta', 'Tarjeta'

    class TipoEntrega(models.TextChoices):
        DOMICILIO = 'domicilio', 'Domicilio'
        RECOGER = 'recoger', 'Recoger en tienda'

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="user"
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

    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
    )

    tipo_entrega = models.CharField(
        max_length=20,
        choices=TipoEntrega.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    def __str__(self):
        return f"Pedido #{self.pk} - {self.user}"
