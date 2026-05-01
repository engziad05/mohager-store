from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Category, Product, ProductVariant, ProductImage, HeroSlide, Cart, CartItem, Order, OrderItem

# 1. تظبيط صور المنتج
class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1

# 2. تظبيط مقاسات المنتج (Variants)
class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1

# 3. تظبيط عرض المنتج في لوحة التحكم
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name_ar', 'category', 'price', 'color', 'is_active']
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
    # الحقول دي قراءة فقط عشان الدقة
    readonly_fields = ['product', 'variant', 'quantity', 'price'] 

# 6. تظبيط عرض الطلبات (الفواتير) - تم تصحيح status هنا
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # غيرنا status لـ is_completed عشان تطابق الموديل بتاعك
    list_display = ['id', 'full_name', 'phone', 'is_completed', 'total_price', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['full_name', 'phone']
    inlines = [OrderItemInline]

# 7. تسجيل باقي الموديلات
@admin.register(HeroSlide)
class HeroSlideAdmin(ModelAdmin):
    list_display = ['title_ar', 'order', 'is_active']
    list_editable = ['order', 'is_active']

@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ['id', 'created_at'] # شيلنا user لو السلة بتشتغل بـ session بس