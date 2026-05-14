from django.conf import settings
from django.db import models


class HeroSlide(models.Model):
    image = models.ImageField(upload_to='hero/', verbose_name='صورة البانر')
    title_ar = models.CharField(max_length=200, verbose_name='العنوان (عربي)')
    subtitle_ar = models.TextField(verbose_name='الوصف (عربي)', blank=True)
    btn_text_ar = models.CharField(max_length=50, default='اطلب الآن', verbose_name='نص الزر (عربي)')
    btn_url = models.CharField(max_length=255, default='/', verbose_name='رابط الزر')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتيب العرض')
    is_active = models.BooleanField(default=True, verbose_name='تفعيل؟')
    action_hint_ar = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='لطلب مُهاجر الآن',
        verbose_name='الجملة التحفيزية فوق الزر (عربي)',
    )

    class Meta:
        ordering = ['order']
        db_table = 'store_heroslide'
        verbose_name = 'بانر الصفحة الرئيسية'
        verbose_name_plural = 'بانرات الصفحة الرئيسية (السلايدر)'

    def __str__(self):
        return self.title_ar


class SavedAddress(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_address',
    )
    phone = models.CharField(max_length=20, verbose_name='رقم التليفون')
    region = models.CharField(max_length=100, verbose_name='المحافظة')
    address = models.CharField(max_length=500, verbose_name='العنوان التفصيلي')
    building = models.CharField(max_length=50, blank=True, null=True, verbose_name='عمارة')
    floor = models.CharField(max_length=50, blank=True, null=True, verbose_name='دور')
    apartment = models.CharField(max_length=50, blank=True, null=True, verbose_name='شقة')
    landmark = models.CharField(max_length=255, blank=True, null=True, verbose_name='علامة مميزة')

    class Meta:
        db_table = 'store_savedaddress'

    def __str__(self):
        return f'عنوان {self.user.first_name or self.user.email}'


class StoreSetting(models.Model):
    shipping_cost = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='تكلفة الشحن',
    )

    class Meta:
        db_table = 'store_storesetting'
        verbose_name = 'Shipping rate'
        verbose_name_plural = 'Shipping rates'

    def __str__(self):
        return f'Shipping rate: {self.shipping_cost} EGP'
