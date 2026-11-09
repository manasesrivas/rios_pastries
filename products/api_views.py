from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, AllowAny

from .models import Product
from .serializers import ProductSerializer

from django.db.models import Q
from categories.models import Category


class ProductListAPIView(ListCreateAPIView):
    queryset = Product.objects.select_related('category')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')

        search = self.request.query_params.get('search', '').strip()
        category_id = self.request.query_params.get('category_id', '').strip()

        # if self.request.user.has_perm('products.change_product'):
        queryset = Product.all_objects.select_related('category')
        # else:
            # queryset = Product.objects.all()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(category__name__icontains=search)
            )

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class ProductDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_qeuryset(self):
        return Product.objects.select_related('category').filter(
            status=Product.StatusProduct.ACTIVO
        )

    def perform_destroy(self, instance):
        instance.status = Product.StatusProduct.ELIMINADO
        instance.save(update_fields=['status'])