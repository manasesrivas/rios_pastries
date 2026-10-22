from django.urls import path
from .views import *
app_name = 'products'

urlpatterns = [
   path('', ProductListView.as_view(), name='list'),
    path('crear/', ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', ProductDeleteView.as_view(), name='delete'),
]