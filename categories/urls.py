
from django.urls import path
from .views import (
    CategoriesListView,
    CategoriesDetailView,
    CategoriesCreateView,
    CategoriesUpdateView,
    CategoriesDeleteView,
)

app_name = 'categories'

urlpatterns = [
    path('', CategoriesListView.as_view(), name='list'),
    path('crear/', CategoriesCreateView.as_view(), name='create'),
    path('<int:pk>/', CategoriesDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', CategoriesUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', CategoriesDeleteView.as_view(), name='delete'),
]
