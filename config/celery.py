import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('mohager_store')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Send daily order summary emails at 9 AM
    'send-daily-order-summary': {
        'task': 'analytics.tasks.send_daily_order_summary',
        'schedule': crontab(hour=9, minute=0),
    },
    # Clean up expired cart items daily at midnight
    'cleanup-expired-carts': {
        'task': 'cart.tasks.cleanup_expired_carts',
        'schedule': crontab(hour=0, minute=0),
    },
    # Update product analytics daily at 1 AM
    'update-product-analytics': {
        'task': 'analytics.tasks.update_product_analytics',
        'schedule': crontab(hour=1, minute=0),
    },
}

app.conf.task_routes = {
    'analytics.tasks.*': {'queue': 'analytics'},
    'cart.tasks.*': {'queue': 'cart'},
    'orders.tasks.*': {'queue': 'orders'},
    'notifications.tasks.*': {'queue': 'notifications'},
}

app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes
