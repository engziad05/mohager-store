from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import CustomUser


class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    model = CustomUser
    
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Mohager profile', {'fields': ('phone', 'preferred_lang')}),
    )
    list_display = ['username', 'email', 'phone', 'preferred_lang', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'preferred_lang']
    search_fields = ['username', 'email', 'phone']
