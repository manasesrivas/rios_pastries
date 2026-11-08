from django.urls import path
from .views import *

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('create/', OrderCreateView.as_view(), name='create'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='status_update'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('update/<int:pk>/', OrderUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', OrderDeleteView.as_view(), name='delete'),
    path('checkout/', OrderCheckoutView.as_view(), name='checkout'),
    path('deliver/', OrderDeliverView.as_view(), name='deliver'),
]