from django.urls import path
from rest_framework_simplejwt.views import *
from .api_view import *

urlpatterns = [
    # Login: recibe username/password y devuelve tokens (access y refresh)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Refresh: recibe el refresh token y devuelve un nuevo access token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),

    path('register/', RegisterView.as_view(), name='auth_register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='auth_verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='auth_resend_otp'),
]