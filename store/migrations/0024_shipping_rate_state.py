from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0023_remove_moved_models_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelTable(
                    name='heroslide',
                    table='store_heroslide',
                ),
                migrations.AlterModelTable(
                    name='savedaddress',
                    table='store_savedaddress',
                ),
                migrations.AlterModelTable(
                    name='storesetting',
                    table='store_storesetting',
                ),
                migrations.AlterModelOptions(
                    name='storesetting',
                    options={
                        'verbose_name': 'Shipping rate',
                        'verbose_name_plural': 'Shipping rates',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
