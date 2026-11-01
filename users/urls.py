from django.urls import path
from . import views
# users/urls.py
app_name='users'
urlpatterns = [
    path('mostrar/', views.UserListView.as_view(), name='allUsers'),
    path('crear/', views.UserCreateView.as_view(), name='createUser'),
    path('<int:pk>/', views.UserUpdateView.as_view(), name='updateUser'),
    path('home/', views.home, name='home') # ---> ruta temporal
]