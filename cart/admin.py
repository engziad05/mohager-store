from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity']


class CartAdmin(ModelAdmin):
    list_display = ['id', 'created_at']
    inlines = [CartItemInline]
