from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from colorama import Fore

User = get_user_model()

# Usuarios de prueba
usuarios = [
    {
        "email": "manases.rivas.3005@gmail.com",
        "password": "admin",
        "nombres": "manases",
        "apellidos": "rivas",
        "grupo": None,
        "superusuario": True,
    },
    {
        "email": "administrador@example.com",
        "password": "Admin123!",
        "nombres": "el admin",
        "apellidos": "Administrador",
        "grupo": "Administrador",
        "superusuario": False,
    },
    {
        "email": "empleado@example.com",
        "password": "Empleado123!",
        "nombres": "empleado",
        "apellidos": "el empleado",
        "grupo": "Empleado",
        "superusuario": False,
    },
    {
        "email": "empleado1@example.com",
        "password": "Empleado123!",
        "nombres": "empleado1",
        "apellidos": "el empleado 1",
        "grupo": "Empleado",
        "superusuario": False,
    },
    {
        "email": "empleado2@example.com",
        "password": "Empleado123!",
        "nombres": "empleado2",
        "apellidos": "el empleado 2",
        "grupo": "Empleado",
        "superusuario": False,
    },
    {
        "email": "cliente@example.com",
        "password": "Cliente123!",
        "nombres": "cliente",
        "apellidos": "Cliente",
        "grupo": "Cliente",
        "superusuario": False,
    },
    {
        "email": "cliente1@example.com",
        "password": "Cliente123!",
        "nombres": "cliente1",
        "apellidos": "el Cliente 1",
        "grupo": "Cliente",
        "superusuario": False,
    },
    {
        "email": "cliente2@example.com",
        "password": "Cliente123!",
        "nombres": "cliente2",
        "apellidos": "el Cliente 2",
        "grupo": "Cliente",
        "superusuario": False,
    },
]


@transaction.atomic
def crear_usuarios():
    for datos in usuarios:
        email = datos["email"]

        # Crear o recuperar el usuario
        usuario = User.objects.filter(email=email).first()

        if usuario is None:
            usuario = User(
                email=email,
                nombres=datos["nombres"],
                apellidos=datos["apellidos"],
            )
            usuario.set_password(datos["password"])
            usuario.save()
            print(f"Usuario creado: {Fore.GREEN}{email}{Fore.RESET}")
        else:
            print(f"El usuario ya existe: {email}")

        # Configurar privilegios de superusuario
        if datos["superusuario"]:
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.save()

        # Asignar grupo
        nombre_grupo = datos["grupo"]

        if nombre_grupo:
            grupo, creado = Group.objects.get_or_create(
                name=nombre_grupo
            )
            usuario.groups.add(grupo)
            print(f"Grupo '{nombre_grupo}' asignado a {email}")

    print("Proceso finalizado.")


crear_usuarios()
