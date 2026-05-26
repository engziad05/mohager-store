from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_product_compare_at_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productvariant',
            name='stock_quantity',
        ),
    ]
