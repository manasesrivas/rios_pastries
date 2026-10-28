from django.db import transaction
from products.models import Product
from utils.products import products
from categories.models import Category

@transaction.atomic
def crear_productos():
    for datos in products:
        nombre = datos["name"]

        category = Category.objects.get(name=datos['category'])


        # Crear o recuperar el producto
        producto, creado = Product.objects.get_or_create(
            name=nombre,
            defaults={
                "image": datos["image"],
                "description": datos["description"],
                "price": datos["price"],
                "category": category,
                "available": datos["available"],
                "stock": datos['stock']
            },
        )

        if creado:
            print(f"Producto creado: {nombre}")
        else:
            print(f"El producto ya existe: {nombre}")

    print("Proceso finalizado.")

crear_productos()