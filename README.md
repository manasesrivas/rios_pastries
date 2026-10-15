# Rios pastries backend


# comandos

para encender el servidor:
```bash
python manage.py runserver
```

## agregar un modulo al proyecto
`djando` trabaja mediante apps, para crear una app necesita escribir el siguiente codigo en la terminal:
```bash
python manage.py startapp [nombre_de_la_app]
```
en el caso en la que se creó la app `users` fue de la siguiente manera: 
```bash
python manage.py startapp users
```
luego registrarlo en el archivo `settings.py` en array `INSTALLED_APPS` agregar debajo la app creada para que django pueda reconocerla

comando para crear la migracion para los roles iniciales
```bash
python manage.py makemigrations [modulo] --empty -n [nombre_migracion]
```

## rutas

