rm -rf db.sqlite3
python manage.py migrate
python manage.py shell < create_users.py
python manage.py runserver