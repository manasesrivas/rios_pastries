from django.urls import path
from .views import (
    ReservationListView,
    ReservationDetailView,
    ReservationCreateView,
    ReservationUpdateView,
    ReservationDeleteView,
)

app_name = 'reservations'

urlpatterns = [
    path('', ReservationListView.as_view(), name='list'),
    path('create/<int:pk>/', ReservationCreateView.as_view(), name='create'),
    path('<int:pk>/', ReservationDetailView.as_view(), name='detail'),
    path('update/<int:pk>/', ReservationUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', ReservationDeleteView.as_view(), name='delete'),
]