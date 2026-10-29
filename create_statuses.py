from detail_orders.models import Status

estados = [
    Status.PENDIENTE,
    Status.ENTREGADO,
    Status.CANCELADO,
]

for estado in estados:
    status, created = Status.objects.get_or_create(name=estado)
    if created:
        print(f"Estado creado: {status.get_name_display()}")
    else:
        print(f"El estado ya existe: {status.get_name_display()}")

