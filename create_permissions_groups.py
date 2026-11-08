
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from colorama import Fore

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
        'app': 'orders',
        'modelo': 'order',
        'permisos': ['view_order', 'add_order', 'change_order', 'delete_order'],
        'grupo': 'Administrador',
    },
    {
        'app': 'venues',
        'modelo': 'venue',
        'permisos': [
            'add_venue', 'view_venue', 'change_venue', 'delete_venue',
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
    {
        'app': 'orders',
        'modelo': 'order',
        'permisos': ['view_order', 'add_order'],
        'grupo': 'Cliente',
    },
    {
        'app': 'halls',
        'modelo': 'hall',
        'permisos': [
            'add_hall', 'view_hall', 'change_hall', 'delete_hall',
        ],
        'grupo': 'Administrador',
    },
    {
        'app': 'halls',
        'modelo': 'hall',
        'permisos': [
            'view_hall'
        ],
        'grupo': 'Cliente',
    },
    {
        'app': 'venues',
        'modelo': 'venue',
        'permisos': ['view_venue'],
        'grupo': 'Cliente',
    },
    {
    'app': 'reservations',
    'modelo': 'reservation',
    'permisos': ['view_reservation', 'add_reservation'],
    'grupo': 'Cliente',
},
{
    'app': 'reservations',
    'modelo': 'reservation',
    'permisos': ['view_reservation', 'add_reservation',
                 'change_reservation', 'delete_reservation'],
    'grupo': 'Administrador',
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
        print(f"{Fore.RED}Permisos no encontrados para {app}.{modelo}: {faltantes}{Fore.RESET}")
        continue

    # Asignar permisos al grupo
    grupo.permissions.add(*permisos)

    print(f"Permisos asignados al grupo: {nombre_grupo}")

print("Proceso finalizado.")