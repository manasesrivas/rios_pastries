from django.urls import path
from .views import *

#roles/urls.py

app_name='roles'
urlpatterns = [
        path('rol/', RolesView.as_view(), name='createRol'),
        path('rol/mostrar/', TodosRolesView.as_view(), name='allRoles'),
]