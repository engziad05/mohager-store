from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser

    fieldsets = UserAdmin.fieldsets + (
        ('Mohager profile', {'fields': ('phone', 'preferred_lang')}),
    )
    list_display = ['username', 'email', 'phone', 'preferred_lang', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'preferred_lang']
    search_fields = ['username', 'email', 'phone']
