from django.db import models

# Create your models here.

class Categories(models.Model):
    name = models.CharField(unique=True)

    def __str__(self):
        return self.name
