from django.urls import path

from .api_views import ReservationCreateAPIView, ReservationListAPIView

app_name = 'reservations_api'

urlpatterns = [
    path('', ReservationListAPIView.as_view(), name='list'),
    path('create/', ReservationCreateAPIView.as_view(), name='create'),
]
