from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_remove_productvariant_stock_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='weight_range',
            field=models.CharField(blank=True, help_text='مثال: 70-85', max_length=50, null=True, verbose_name='الوزن (من-إلى)'),
        ),
    ]
