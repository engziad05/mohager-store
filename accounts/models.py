from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # اختيارات اللغة
    LANGUAGE_CHOICES = [
        ('ar', 'العربية'),
        ('en', 'English'),
    ]
    
    # الحقول الجديدة اللي الخطة طلبتها
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم التليفون")
    preferred_lang = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='ar', verbose_name="اللغة المفضلة")

    def __str__(self):
        return self.username


class StaffUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = "مشرف (Staff)"
        verbose_name_plural = "المشرفين (Staff)"