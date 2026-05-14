# State-only: tables remain; ownership moves to products / orders / cart apps.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_alter_order_options_alter_product_options_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='OrderItem'),
                migrations.DeleteModel(name='CartItem'),
                migrations.DeleteModel(name='Order'),
                migrations.DeleteModel(name='Cart'),
                migrations.DeleteModel(name='ProductImage'),
                migrations.DeleteModel(name='ProductVariant'),
                migrations.DeleteModel(name='Product'),
                migrations.DeleteModel(name='Category'),
            ],
            database_operations=[],
        ),
    ]
