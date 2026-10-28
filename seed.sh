rm -rf db.sqlite3
python manage.py migrate
python manage.py shell < create_users.py
<<<<<<< HEAD
python manage.py shell < create_products.py
=======
<<<<<<< Updated upstream
=======
python manage.py shell < create_categories.py
python manage.py shell < create_products.py
>>>>>>> Stashed changes
>>>>>>> feature/products
python manage.py runserver