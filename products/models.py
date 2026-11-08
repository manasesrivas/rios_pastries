from django.db import models
from categories.models import Category
from cloudinary.models import CloudinaryField

# Create your models here.
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

    def __str__(self):
        return self.name
