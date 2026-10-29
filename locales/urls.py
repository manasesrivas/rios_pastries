from django.urls import path
from .views import (
    SalaListView,
    SalaDetailView,
    SalaCreateView,
    SalaUpdateView,
    SalaDeleteView,
)

app_name = 'locales'

urlpatterns = [
    path('', SalaListView.as_view(), name='list'),
    path('<int:pk>/', SalaDetailView.as_view(), name='detail'),
    path('create/', SalaCreateView.as_view(), name='create'),
    path('update/<int:pk>', SalaUpdateView.as_view(), name='update'),
    path('delete/<int:pk>', SalaDeleteView.as_view(), name='delete'),
]

