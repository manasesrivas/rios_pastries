from django.urls import path

from .api_views import HallDetailAPIView, HallListAPIView

app_name = 'halls_api'

urlpatterns = [
    path('', HallListAPIView.as_view(), name='list'),
    path('<int:pk>/', HallDetailAPIView.as_view(), name='detail'),
]