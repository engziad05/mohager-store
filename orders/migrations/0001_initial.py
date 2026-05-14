import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Order',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('tracking_no', models.CharField(blank=True, max_length=50, null=True, verbose_name='رقم الطلب')),
                        ('full_name', models.CharField(max_length=255, verbose_name='الاسم بالكامل')),
                        ('phone', models.CharField(max_length=20, verbose_name='رقم التليفون')),
                        ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='الإيميل')),
                        ('region', models.CharField(default='-', max_length=100, verbose_name='المحافظة')),
                        ('address', models.CharField(max_length=500, verbose_name='العنوان')),
                        ('building', models.CharField(default='-', max_length=50, verbose_name='عمارة')),
                        ('floor', models.CharField(default='-', max_length=50, verbose_name='دور')),
                        ('apartment', models.CharField(default='-', max_length=50, verbose_name='شقة')),
                        ('landmark', models.CharField(blank=True, max_length=255, null=True, verbose_name='علامة مميزة')),
                        ('status', models.CharField(choices=[('Pending', 'قيد الانتظار'), ('Processing', 'جاري التجهيز'), ('Shipped', 'تم الشحن'), ('Delivered', 'تم التوصيل'), ('Cancelled', 'ملغي')], default='Pending', max_length=20, verbose_name='حالة الطلب')),
                        ('total_price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='إجمالي الحساب')),
                        ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')),
                        ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={'db_table': 'store_order'},
                ),
                migrations.CreateModel(
                    name='OrderItem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('quantity', models.PositiveIntegerField(default=1, verbose_name='الكمية')),
                        ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='السعر وقت الشراء')),
                        ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order', verbose_name='الطلب')),
                        ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.product', verbose_name='المنتج')),
                        ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.productvariant', verbose_name='المتغير (مقاس/لون)')),
                    ],
                    options={'db_table': 'store_orderitem'},
                ),
            ],
            database_operations=[],
        ),
    ]
