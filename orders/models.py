import random
import string

from django.conf import settings
from django.db import models

from products.models import Product, MasterStockVariant


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'قيد الانتظار'),
        ('Processing', 'جاري التجهيز'),
        ('Shipped', 'تم الشحن'),
        ('Delivered', 'تم التوصيل'),
        ('Cancelled', 'ملغي'),
    )
    tracking_no = models.CharField(max_length=50, null=True, blank=True, verbose_name='رقم الطلب')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=255, verbose_name='الاسم بالكامل')
    phone = models.CharField(max_length=20, verbose_name='رقم التليفون')
    email = models.EmailField(blank=True, null=True, verbose_name='الإيميل')
    region = models.CharField(max_length=100, default='-', verbose_name='المحافظة')
    address = models.CharField(max_length=500, verbose_name='العنوان')
    building = models.CharField(max_length=50, default='-', verbose_name='عمارة')
    floor = models.CharField(max_length=50, default='-', verbose_name='دور')
    apartment = models.CharField(max_length=50, default='-', verbose_name='شقة')
    landmark = models.CharField(max_length=255, blank=True, null=True, verbose_name='علامة مميزة')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        verbose_name='حالة الطلب',
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الحساب',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')

    class Meta:
        db_table = 'store_order'

    def save(self, *args, **kwargs):
        if not self.tracking_no:
            chars = string.ascii_uppercase + string.digits
            random_str = ''.join(random.choice(chars) for _ in range(6))
            self.tracking_no = f'MHG-{random_str}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'طلب رقم {self.id} - {self.full_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='الطلب',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='المنتج',
    )
    variant = models.ForeignKey(
        'products.MasterStockVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='المتغير (مقاس/لون)',
    )
    product_color = models.ForeignKey(
        'products.ProductColor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='اللون',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='الكمية')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='السعر وقت الشراء')

    class Meta:
        db_table = 'store_orderitem'

    def __str__(self):
        if self.product:
            return f'{self.quantity} x {self.product.name_en} - طلب #{self.order.id}'
        return f'عنصر محذوف - طلب #{self.order.id}'
