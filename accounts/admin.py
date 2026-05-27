from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import CustomUser, StaffUser


class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    model = CustomUser
    
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Mohager profile', {'fields': ('phone', 'preferred_lang')}),
    )
    list_display = ['username', 'email', 'phone', 'preferred_lang', 'is_staff', 'is_active']
    list_filter = ['is_active', 'preferred_lang']
    search_fields = ['username', 'email', 'phone']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False, is_superuser=False)


class StaffUserAdmin(BaseUserAdmin, ModelAdmin):
    model = StaffUser
    
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Mohager profile', {'fields': ('phone', 'preferred_lang')}),
    )
    list_display = ['username', 'email', 'phone', 'preferred_lang', 'is_staff', 'is_superuser', 'is_active']
    list_filter = ['is_superuser', 'is_active', 'preferred_lang']
    search_fields = ['username', 'email', 'phone']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)
