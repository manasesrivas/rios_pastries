from django.contrib.auth import get_user_model
User = get_user_model()
superuser = \
    {
        "email": "manases.rivas.3005@gmail.com",
        "password": "admin",
        "nombres": "manases",
        "apellidos": "rivas",
        "grupo": None,
        "superusuario": True,
    }

usuario = User(
    email=superuser['email'],
    nombres=superuser["nombres"],
    apellidos=superuser["apellidos"],
)
usuario.set_password(superuser["password"])
usuario.is_staff = True
usuario.is_superuser = True
usuario.save()