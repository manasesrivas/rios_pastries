from django.db import models
from categories.models import Category
from cloudinary.models import CloudinaryField

class StatusProduct(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    ELIMINADO = 'eliminado', 'Eliminado'

class ActiveProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=StatusProduct.ACTIVO,
            category__status=Category.Status.ACTIVO
        ).order_by('id')

class Product(models.Model):
    name = models.CharField(max_length=100)
    image = CloudinaryField(
        blank=True,
        null=True,
        folder='/rios_pastries',
        transformation={
        },
        format='webp'
    )
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    available = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=StatusProduct.choices,
        default=StatusProduct.ACTIVO,
    )

    all_objects = models.Manager()
    objects = ActiveProductManager()

    def __str__(self):
        return self.name
