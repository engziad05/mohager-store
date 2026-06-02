import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("UPDATE store_cartitem SET variant_id = NULL;")
    cursor.execute("UPDATE store_orderitem SET variant_id = NULL;")
    
print("Successfully set variant_id to NULL in cart items and order items.")
