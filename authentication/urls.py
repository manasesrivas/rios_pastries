from django.urls import path
from . import views
#authentication/urls.py
app_name='authentication'
urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.UsersCreateView.as_view(), name='register')
]