from django.db import models
from orders.models import Order
from products.models import Product

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
