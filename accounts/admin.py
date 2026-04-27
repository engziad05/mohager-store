from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # هنا بنقول للوحة التحكم تعرض الحقول الجديدة بتاعتنا
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية (مُهاجر)', {'fields': ('phone', 'preferred_lang')}),
    )
    
    # دي العماويد اللي هتظهر في الجدول من بره
    list_display = ['username', 'email', 'phone', 'preferred_lang', 'is_staff']

# تسجيل الجدول في اللوحة
admin.site.register(CustomUser, CustomUserAdmin)