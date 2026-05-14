from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Product, Category, ProductVariant, HeroSlide,
    ProductImage, Order, OrderItem, Cart, CartItem,
)
from .models import StoreSetting


# ==========================================
# 1. أقسام المنتجات (Inlines first, then Admin)
# ==========================================

# صور المنتج الإضافية
class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


# مقاسات وألوان المنتج (Variants)
class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


# تظبيط عرض المنتج الأساسي
class ProductAdmin(ModelAdmin):
    list_display = ['name_ar', 'category', 'base_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name_ar', 'name_en']
    inlines = [ProductVariantInline, ProductImageInline]


# ==========================================
# 2. الأقسام (Category)
# ==========================================
class CategoryAdmin(ModelAdmin):
    list_display = ['name_ar', 'name_en', 'is_active']
    prepopulated_fields = {'slug': ('name_en',)}


# ==========================================
# 3. دورة الطلبات (Inlines first, then Admin)
# ==========================================

# تفاصيل المنتجات جوه الفاتورة (Inline)
class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity', 'price']


# عرض الطلبات الأساسية (Admin)
class OrderAdmin(ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at', 'region']
    search_fields = ['full_name', 'phone', 'id']
    inlines = [OrderItemInline]
    list_display_links = ['id', 'full_name']


# ==========================================
# 4. واجهة المستخدم والتسوق (Sliders, Carts)
# ==========================================

# البانر الرئيسي (Slider)
class HeroSlideAdmin(ModelAdmin):
    list_display = ['title_ar', 'order', 'is_active']
    list_editable = ['order', 'is_active']


# المنتجات جوه السلة النشطة (Inline)
class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity']


# عرض السلال النشطة
class CartAdmin(ModelAdmin):
    list_display = ['id', 'created_at']
    inlines = [CartItemInline]


# إعدادات المتجر
class StoreSettingAdmin(ModelAdmin):
    list_display = ['__str__']
