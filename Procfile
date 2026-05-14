web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi --log-file -
worker: celery -A config worker -l info -Q default,notifications,orders,analytics,cart
