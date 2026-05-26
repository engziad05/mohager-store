web: python manage.py migrate --noinput && python manage.py ensure_superuser && python manage.py collectstatic --noinput && gunicorn config.wsgi --workers 2 --threads 4 --worker-class gthread --timeout 120 --log-file -
worker: celery -A config worker -l info -Q default,notifications,orders,analytics,cart
