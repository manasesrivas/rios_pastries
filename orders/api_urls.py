from django.urls import path

from .api_views import OrderListCreateAPIView, ValidateCartAPIView

app_name = 'orders_api'

urlpatterns = [
    path('validate/', ValidateCartAPIView.as_view(), name='validate-cart'),
    path('', OrderListCreateAPIView.as_view(), name='list_create'),
]
