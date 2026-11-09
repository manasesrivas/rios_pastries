from django.core.validators import MinValueValidator
from reservations.models import Reservation
from django.db import models
from products.models import Product

class ReservationItem(models.Model):
    """Productos seleccionados específicamente para el evento"""
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reservation', 'product'],
                name='unique_product_per_reservation',
            ),
        ]

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad}x {self.product.name} (Reserva #{self.reservation.pk})"