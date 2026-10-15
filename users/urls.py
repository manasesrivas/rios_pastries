from django.urls import path
from . import views
# users/urls.py
app_name='users'
urlpatterns = [
    path('mostrar/', views.TodosUsuariosView.as_view(), name='allUsers'),
    path('crear/', views.AgregarUsuario.as_view(), name='createUser'),
    path('<int:pk>/', views.UserUpdate.as_view(), name='updateUser'),
    path('home/', views.home, name='home') # ---> ruta temporal
]