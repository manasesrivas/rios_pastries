rm -rf db.sqlite3
python manage.py migrate
python manage.py shell < create_users.py
<<<<<<< Updated upstream
=======
python manage.py shell < create_categories.py
python manage.py shell < create_products.py
>>>>>>> Stashed changes
python manage.py runserver