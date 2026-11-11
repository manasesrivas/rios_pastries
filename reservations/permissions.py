def can_manage_reservations(user):
    return (
        user.is_superuser
        or user.is_staff
        or user.groups.filter(name__in=['Administrador', 'Cajero']).exists()
    )
