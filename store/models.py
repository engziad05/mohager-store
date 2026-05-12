from django.conf import settings
from django.db import models
import random
import string


# 1. جدول الأقسام (Categories)
class Category(models.Model):
    name_ar = models.CharField(max_length=100, verbose_name="الاسم (عربي)")
    name_en = models.CharField(max_length=100, verbose_name="الاسم (إنجليزي)")
    slug = models.SlugField(unique=True) 
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name_en

# 2. جدول المنتجات الأساسية (Products)
class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name_ar = models.CharField(max_length=200, verbose_name="اسم المنتج (عربي)")
    name_en = models.CharField(max_length=200, verbose_name="اسم المنتج (إنجليزي)")
    description_ar = models.TextField(verbose_name="الوصف (عربي)", blank=True)
    description_en = models.TextField(verbose_name="الوصف (إنجليزي)", blank=True)
    color_ar = models.CharField(max_length=50, blank=True, null=True, verbose_name="اللون (عربي)")
    color_en = models.CharField(max_length=50, blank=True, null=True, verbose_name="اللون (إنجليزي)")
    color_code = models.CharField(max_length=20, verbose_name="كود اللون (Hex)", default="#111111")
    # السعر الأساسي والثابت لكل المتغيرات
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="السعر الأساسي") 
    image = models.ImageField(upload_to='products/', verbose_name="صورة المنتج", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.name_en

# 3. جدول الصور المتعددة للمنتج (عشان تظهر كـ Inline في الأدمن)
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/', verbose_name="الصورة الإضافية")

    def __str__(self):
        return f"صورة إضافية لـ {self.product.name_en}"

# 4. جدول متغيرات المنتج (Product Variants - المقاسات والألوان)
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, blank=True, null=True, verbose_name="المقاس") 
    stock = models.PositiveIntegerField(default=0, verbose_name="المخزون")

    def __str__(self):
        return f"{self.product.name_en} - {self.size} - {self.product.color_en}"

# 5. البانر الرئيسي (Hero Slide)
class HeroSlide(models.Model):
    image = models.ImageField(upload_to='hero/', verbose_name="صورة البانر")
    title_ar = models.CharField(max_length=200, verbose_name="العنوان (عربي)")
    subtitle_ar = models.TextField(verbose_name="الوصف (عربي)", blank=True)
    btn_text_ar = models.CharField(max_length=50, default="اطلب الآن", verbose_name="نص الزر (عربي)")
    btn_url = models.CharField(max_length=255, default="/", verbose_name="رابط الزر")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    is_active = models.BooleanField(default=True, verbose_name="تفعيل؟")
    action_hint_ar = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        default="لطلب مُهاجر الآن", 
        verbose_name="الجملة التحفيزية فوق الزر (عربي)"
    )

    class Meta:
        ordering = ['order']
        verbose_name = "بانر الصفحة الرئيسية"
        verbose_name_plural = "بانرات الصفحة الرئيسية (السلايدر)"

    def __str__(self):
        return self.title_ar

# 6. موديل السلة (Cart)
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سلة رقم {self.id}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

# 7. عناصر السلة (Cart Items)
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True) 
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name_en}"

    @property
    def total_price(self):
        # 🚨 التعديل هنا: السعر بيتحسب من المنتج الأساسي علطول
        return self.product.base_price * self.quantity

# 8. جدول الطلبات (Orders)
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'قيد الانتظار'),
        ('Processing', 'جاري التجهيز'),
        ('Shipped', 'تم الشحن'),
        ('Delivered', 'تم التوصيل'),
        ('Cancelled', 'ملغي'),
    )
    tracking_no = models.CharField(max_length=50, null=True, blank=True, verbose_name="رقم الطلب")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name="الاسم بالكامل")
    phone = models.CharField(max_length=20, verbose_name="رقم التليفون")
    email = models.EmailField(blank=True, null=True, verbose_name="الإيميل")
    region = models.CharField(max_length=100, default="-", verbose_name="المحافظة")
    address = models.CharField(max_length=500, verbose_name="العنوان")
    building = models.CharField(max_length=50, default="-", verbose_name="عمارة")
    floor = models.CharField(max_length=50, default="-", verbose_name="دور")
    apartment = models.CharField(max_length=50, default="-", verbose_name="شقة")
    landmark = models.CharField(max_length=255, blank=True, null=True, verbose_name="علامة مميزة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="حالة الطلب")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="إجمالي الحساب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    
    def save(self, *args, **kwargs):
        if not self.tracking_no:  
            chars = string.ascii_uppercase + string.digits 
            random_str = ''.join(random.choice(chars) for _ in range(6)) 
            self.tracking_no = f"MHG-{random_str}" 
            
        super(Order, self).save(*args, **kwargs)

    def __str__(self):
        return f"طلب رقم {self.id} - {self.full_name}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['tracking_no']),
        ]

# 9. جدول عناصر الطلب (Order Items)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="الطلب")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="المنتج")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المتغير (مقاس/لون)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر وقت الشراء")

    def __str__(self):
        if self.product:
            return f"{self.quantity} x {self.product.name_en} - طلب #{self.order.id}"
        return f"عنصر محذوف - طلب #{self.order.id}"

# 10. جدول العنوان المحفوظ للعميل
class SavedAddress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_address')
    phone = models.CharField(max_length=20, verbose_name="رقم التليفون")
    region = models.CharField(max_length=100, verbose_name="المحافظة")
    address = models.CharField(max_length=500, verbose_name="العنوان التفصيلي")
    building = models.CharField(max_length=50, blank=True, null=True, verbose_name="عمارة")
    floor = models.CharField(max_length=50, blank=True, null=True, verbose_name="دور")
    apartment = models.CharField(max_length=50, blank=True, null=True, verbose_name="شقة")
    landmark = models.CharField(max_length=255, blank=True, null=True, verbose_name="علامة مميزة")

    def __str__(self):
        return f"عنوان {self.user.first_name or self.user.email}"

# 11. إعدادات المتجر
class StoreSetting(models.Model):
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="تكلفة الشحن")
    
    def __str__(self):
        return "إعدادات المتجر"
        
    class Meta:
        verbose_name = "إعداد المتجر"
        verbose_name_plural = "إعدادات المتجر"