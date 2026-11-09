from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .api_view import *

urlpatterns = [
    # Login: recibe username/password y devuelve tokens (access y refresh)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Refresh: recibe el refresh token y devuelve un nuevo access token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
]