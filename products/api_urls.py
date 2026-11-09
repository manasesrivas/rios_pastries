from django.urls import path

from .api_views import ProductDetailAPIView, ProductListAPIView

app_name = 'products_api'

urlpatterns = [
    path('', ProductListAPIView.as_view(), name='list'),
    path('<int:pk>/', ProductDetailAPIView.as_view(), name='detail'),
]
