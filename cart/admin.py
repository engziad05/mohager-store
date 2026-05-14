from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity']


class CartAdmin(ModelAdmin):
    list_display = ['id', 'user', 'item_count', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__username']
    list_select_related = ['user']
    inlines = [CartItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = 'Items'
