from unfold.admin import ModelAdmin, TabularInline

from .models import Category, Product, ProductImage, ProductVariant, ProductPrint


class ProductPrintInline(TabularInline):
    model = ProductPrint
    extra = 1


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductAdmin(ModelAdmin):
    list_display = ['name_en', 'category', 'base_price', 'compare_at_price', 'discount_percent_display', 'stock_summary', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name_ar', 'name_en']
    list_select_related = ['category']
    readonly_fields = ['discount_percent_display']
    fieldsets = (
        ('Product details', {
            'fields': ('category', 'name_ar', 'name_en', 'description_ar', 'description_en', 'image', 'is_active')
        }),
        ('Pricing', {
            'fields': ('base_price', 'compare_at_price', 'discount_percent_display'),
            'description': 'Base price is the final selling price. Original price is shown as crossed-out when it is higher than base price.',
        }),
        ('Color', {
            'fields': ('color_ar', 'color_en', 'color_code')
        }),
    )
    inlines = [ProductVariantInline, ProductPrintInline, ProductImageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').prefetch_related('variants')

    def stock_summary(self, obj):
        total_stock = sum(variant.stock for variant in obj.variants.all())
        return total_stock

    stock_summary.short_description = 'Stock'

    def discount_percent_display(self, obj):
        if not obj or not obj.has_discount:
            return 'No discount'
        return f'{obj.discount_percent}%'

    discount_percent_display.short_description = 'Discount'


class CategoryAdmin(ModelAdmin):
    list_display = ['name_en', 'name_ar', 'is_active']
    search_fields = ['name_ar', 'name_en', 'slug']
    prepopulated_fields = {'slug': ('name_en',)}
