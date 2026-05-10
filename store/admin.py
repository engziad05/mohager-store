from django.contrib import admin
# نستخدم TabularInline و ModelAdmin من Unfold لشكل فخم
from unfold.admin import ModelAdmin, TabularInline 
# استيراد كل الموديلز بما فيهم Cart و CartItem
from .models import (
    Product, Category, ProductVariant, HeroSlide, 
    ProductImage, Order, OrderItem, Cart, CartItem
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
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name_ar', 'category', 'base_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name_ar', 'name_en']
    # نربط الـ Inlines اللي عرفناهم فوق
    inlines = [ProductVariantInline, ProductImageInline] 


# ==========================================
# 2. الأقسام (Category)
# ==========================================
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name_ar', 'name_en', 'is_active']
    # الـ slug يتملي أوتوماتيك من الاسم الإنجليزي
    prepopulated_fields = {'slug': ('name_en',)}


# ==========================================
# 3. دورة الطلبات (Inlines first, then Admin)
# ==========================================

# تفاصيل المنتجات جوه الفاتورة (Inline)
class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    # قراءة فقط لحماية الفاتورة من التعديل العرضي
    readonly_fields = ['product', 'variant', 'quantity', 'price'] 

# عرض الطلبات الأساسية (Admin)
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # حالة الطلب واضحة
    list_display = ['id', 'full_name', 'phone', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at', 'region']
    # البحث باسم العميل، رقمه، أو رقم الطلب
    search_fields = ['full_name', 'phone', 'id']
    inlines = [OrderItemInline] # نربط المنتجات بالأوردر


# ==========================================
# 4. واجهة المستخدم والتسوق (Sliders, Carts)
# ==========================================

# البانر الرئيسي (Slider)
@admin.register(HeroSlide)
class HeroSlideAdmin(ModelAdmin):
    list_display = ['title_ar', 'order', 'is_active']
    list_editable = ['order', 'is_active'] # تعديل الترتيب من الجدول بره

# المنتجات جوه السلة النشطة (Inline)
class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity'] # قراءة فقط للسلامة

# عرض السلال النشطة
@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ['id', 'created_at']
    inlines = [CartItemInline] 
    
admin.site.register(StoreSetting)