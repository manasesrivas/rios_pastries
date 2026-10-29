from django.db import models
from orders.models import Order
from products.models import Product


class Status(models.Model):
    PENDIENTE = 'pendiente'
    ENTREGADO = 'entregado'
    CANCELADO = 'cancelado'

    STATUS_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (ENTREGADO, 'Entregado'),
        (CANCELADO, 'Cancelado'),
    ]

    name = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDIENTE,
        unique=True
    )

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

    def __str__(self):
        return self.get_name_display()


class DetailOrder(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="product"
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name="detail_orders",
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_producto_por_pedido"
            )
        ]

    def __str__(self):
        return (
            f"{self.product} x {self.quantity}"
        )
