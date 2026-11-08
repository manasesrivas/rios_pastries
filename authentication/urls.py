from django.urls import path
from . import views
from django.views.generic import TemplateView
#authentication/urls.py
app_name='authentication'
urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.UsersCreateView.as_view(), name='register'),
    path('verification-sent/', TemplateView.as_view(
        template_name='authentication/verification_sent.html',
    ), name='verification_sent'),
    path('activate/<uidb64>/<token>/', views.ActivateAccountView.as_view(), name='activate'),
]