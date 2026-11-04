python manage.py tailwind install
python manage.py tailwind build
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py shell < create_superuser.py
python manage.py shell < create_permissions_groups.py
daphne -b 0.0.0.0 -p $PORT rios_pastries_backend.asgi:application