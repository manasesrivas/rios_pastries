from utils.categories import categories
from products.models import Category

def crear_categorias():
    for categoria in categories:
        category, created = Category.objects.get_or_create(
            name=categoria
        )
        print(f'category created: {category}')

crear_categorias()
