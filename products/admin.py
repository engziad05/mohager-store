from unfold.admin import ModelAdmin, TabularInline

from .models import Category, Product, ProductImage, ProductVariant


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductAdmin(ModelAdmin):
    list_display = ['name_ar', 'category', 'base_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name_ar', 'name_en']
    inlines = [ProductVariantInline, ProductImageInline]


class CategoryAdmin(ModelAdmin):
    list_display = ['name_ar', 'name_en', 'is_active']
    prepopulated_fields = {'slug': ('name_en',)}
