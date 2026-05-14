import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0023_remove_moved_models_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Category',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name_ar', models.CharField(max_length=100, verbose_name='الاسم (عربي)')),
                        ('name_en', models.CharField(max_length=100, verbose_name='الاسم (إنجليزي)')),
                        ('slug', models.SlugField(unique=True)),
                        ('is_active', models.BooleanField(default=True)),
                    ],
                    options={
                        'db_table': 'store_category',
                        'verbose_name': 'Category',
                        'verbose_name_plural': 'Categories',
                    },
                ),
                migrations.CreateModel(
                    name='Product',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name_ar', models.CharField(max_length=200, verbose_name='اسم المنتج (عربي)')),
                        ('name_en', models.CharField(max_length=200, verbose_name='اسم المنتج (إنجليزي)')),
                        ('description_ar', models.TextField(blank=True, verbose_name='الوصف (عربي)')),
                        ('description_en', models.TextField(blank=True, verbose_name='الوصف (إنجليزي)')),
                        ('color_ar', models.CharField(blank=True, max_length=50, null=True, verbose_name='اللون (عربي)')),
                        ('color_en', models.CharField(blank=True, max_length=50, null=True, verbose_name='اللون (إنجليزي)')),
                        ('color_code', models.CharField(default='#111111', max_length=20, verbose_name='كود اللون (Hex)')),
                        ('base_price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='السعر الأساسي')),
                        ('image', models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='صورة المنتج')),
                        ('is_active', models.BooleanField(default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.category')),
                    ],
                    options={'db_table': 'store_product'},
                ),
                migrations.CreateModel(
                    name='ProductImage',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('image', models.ImageField(upload_to='products/gallery/', verbose_name='الصورة الإضافية')),
                        ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='products.product')),
                    ],
                    options={'db_table': 'store_productimage'},
                ),
                migrations.CreateModel(
                    name='ProductVariant',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('size', models.CharField(blank=True, max_length=10, null=True, verbose_name='المقاس')),
                        ('stock_quantity', models.PositiveIntegerField(default=0, verbose_name='الكمية في المخزن')),
                        ('stock', models.PositiveIntegerField(default=0, verbose_name='المخزون')),
                        ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='products.product')),
                    ],
                    options={'db_table': 'store_productvariant'},
                ),
            ],
            database_operations=[],
        ),
    ]
