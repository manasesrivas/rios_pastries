from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .api_view import *

urlpatterns = [
    # path('profile/', ),
]