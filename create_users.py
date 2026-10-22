from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

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
        "email": "cliente@example.com",
        "password": "Cliente123!",
        "nombres": "cliente",
        "apellidos": "Cliente",
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
            print(f"Usuario creado: {email}")
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

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

configuracion_permisos = [
    {
        'app': 'users',
        'modelo': 'user',
        'permisos': [
            'add_user', 'view_user', 'change_user', 'delete_user',
        ],
        'grupo': 'Administrador',
    },
    {
        'app': 'products',
        'modelo': 'product',
        'permisos': [
            'add_product', 'view_product',
            'change_product', 'delete_product'
        ],
        'grupo': 'Administrador',
    },
    {
        'app': 'categories',
        'modelo': 'category',
        'permisos': [
            'add_category', 'view_category',
            'change_category', 'delete_category'
        ],
        'grupo': 'Administrador',
    },
    {
        'app': 'products',
        'modelo': 'product',
        'permisos': ['view_product'],
        'grupo': 'Cliente',
    },
    {
        'app': 'products',
        'modelo': 'product',
        'permisos': [
            'view_product', 'add_product', 'change_product'
        ],
        'grupo': 'Empleado',
    },
]

for configuracion in configuracion_permisos:
    app = configuracion['app']
    modelo = configuracion['modelo']
    permisos_codename = configuracion['permisos']
    nombre_grupo = configuracion['grupo']

    # Obtener o crear el grupo
    grupo, _ = Group.objects.get_or_create(name=nombre_grupo)

    # Obtener el tipo de contenido
    content_type, _ = ContentType.objects.get_or_create(
        app_label=app,
        model=modelo,
    )

    # Buscar los permisos correspondientes
    permisos = Permission.objects.filter(
        content_type=content_type,
        codename__in=permisos_codename,
    )

    # Comprobar que existan todos los permisos solicitados
    encontrados = set(permisos.values_list('codename', flat=True))
    faltantes = set(permisos_codename) - encontrados

    if faltantes:
        print(f"Permisos no encontrados para {app}.{modelo}: {faltantes}")
        continue

    # Asignar permisos al grupo
    grupo.permissions.add(*permisos)

    print(f"Permisos asignados al grupo: {nombre_grupo}")

print("Proceso finalizado.")