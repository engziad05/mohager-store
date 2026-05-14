from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity', 'price']


class OrderAdmin(ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at', 'region']
    search_fields = ['full_name', 'phone', 'id']
    inlines = [OrderItemInline]
    list_display_links = ['id', 'full_name']
