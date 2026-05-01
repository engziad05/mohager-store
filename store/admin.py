from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Category, Product, ProductVariant, ProductImage, HeroSlide, Cart, CartItem, Order, OrderItem

# 1. تظبيط صور المنتج الإضافية
class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1

# 2. تظبيط مقاسات وألوان المنتج (Variants)
class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1

# 3. تظبيط عرض المنتج في لوحة التحكم
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    # شيلنا color وغيرنا price لـ base_price عشان تطابق الموديل الجديد
    list_display = ['name_ar', 'category', 'base_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name_ar', 'name_en']
    inlines = [ProductVariantInline, ProductImageInline]

# 4. تظبيط الأقسام
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name_ar', 'name_en', 'is_active']
    prepopulated_fields = {'slug': ('name_en',)}

# 5. تظبيط تفاصيل الطلب جوه الفاتورة
class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    # الحقول دي قراءة فقط عشان محدش يلعب في الفاتورة بعد ما تتدفع
    readonly_fields = ['product', 'variant', 'quantity', 'price'] 

# 6. تظبيط عرض الطلبات (الفواتير)
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # رجعنا status بدل is_completed عشان دورة حياة الطلب تبقى واضحة
    list_display = ['id', 'full_name', 'phone', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at', 'region']
    search_fields = ['full_name', 'phone']
    inlines = [OrderItemInline]

# 7. تسجيل البانر الرئيسي
@admin.register(HeroSlide)
class HeroSlideAdmin(ModelAdmin):
    list_display = ['title_ar', 'order', 'is_active']
    list_editable = ['order', 'is_active']

# 8. تسجيل السلة
@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ['id', 'created_at']