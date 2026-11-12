python3 manage.py tailwind build
python3 manage.py collectstatic --noinput
python3 manage.py migrate
python3 manage.py shell < create_superuser.py

python3 manage.py shell < create_permissions_groups.py
python3 manage.py shell < create_categories.py
python3 manage.py shell < create_products.py
python3 manage.py shell < create_venue_and_halls.py