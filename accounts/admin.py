from django.contrib.auth.admin import UserAdmin

from common.admin import mohager_admin
from .models import CustomUser


@mohager_admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # الحقول الجديدة بتاعتنا
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية (مُهاجر)', {'fields': ('phone', 'preferred_lang')}),
    )

    # الأعمدة اللي هتظهر في الجدول من بره
    list_display = ['username', 'email', 'phone', 'preferred_lang', 'is_staff']
