from django.urls import path

from .api_views import ReservationListAPIView

app_name = 'reservations_api'

urlpatterns = [
    path('', ReservationListAPIView.as_view(), name='list'),
]
