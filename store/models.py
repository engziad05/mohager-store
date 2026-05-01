from django.conf import settings
from django.db import models

# 1. جدول الأقسام (Categories)
# 1. جدول الأقسام (Categories)
class Category(models.Model):
    name_ar = models.CharField(max_length=100, verbose_name="الاسم (عربي)")
    name_en = models.CharField(max_length=100, verbose_name="الاسم (إنجليزي)")
    slug = models.SlugField(unique=True) # اللينك بتاع القسم
    is_active = models.BooleanField(default=True)

    # التعديل أهو عشان نصلح الاسم في اللوحة
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name_en

# 2. جدول المنتجات الأساسية (Products)
class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    # كلود نصح بـ Bilingual columns (عواميد مزدوجة للغات)
    name_ar = models.CharField(max_length=200, verbose_name="اسم المنتج (عربي)")
    name_en = models.CharField(max_length=200, verbose_name="اسم المنتج (إنجليزي)")
    description_ar = models.TextField(verbose_name="الوصف (عربي)", blank=True)
    description_en = models.TextField(verbose_name="الوصف (إنجليزي)", blank=True)
    price = models.IntegerField(default=0, verbose_name="السعر")
    image = models.ImageField(upload_to='products/', verbose_name="صورة المنتج", blank=True, null=True)
    color = models.CharField(max_length=50, verbose_name="اللون", default="أسود")
    color_code = models.CharField(max_length=20, verbose_name="كود اللون (Hex)", default="#111111")
    
    
    # الـ Soft Delete (بدل ما نمسح المنتج بنخليه False عشان الفواتير القديمة متضربش)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name_en
    

class HeroSlide(models.Model):
    # صورة البانر (هتترفع في فولدر جديد اسمه 'hero/')
    image = models.ImageField(upload_to='hero/', verbose_name="صورة البانر")
    # العنوان الكبير (زي "مُهاجر" أو "الصيفي متاح الآن" في الصور)
    title_ar = models.CharField(max_length=200, verbose_name="العنوان (عربي)")
    # الوصف الصغير اللي تحت العنوان
    subtitle_ar = models.TextField(verbose_name="الوصف (عربي)", blank=True)
    # نص الزرار (زي "اطلب الآن" أو "اكتشف الكوليكشن")
    btn_text_ar = models.CharField(max_length=50, default="اطلب الآن", verbose_name="نص الزر (عربي)")
    # الرابط اللي الزرار هيروحله (مثلاً /#products عشان ينزل للمنتجات)
    btn_url = models.CharField(max_length=255, default="/", verbose_name="رابط الزر")
    # رقم للترتيب (عشان تحدد مين يظهر الأول 1، 2، 3...)
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    # صح لو عايز البانر يظهر، شيل الصح لو عايز تخفيه مؤقتاً
    is_active = models.BooleanField(default=True, verbose_name="تفعيل؟")

    class Meta:
        ordering = ['order'] # عشان يرتبهم بالرقم تلقائياً
        verbose_name = "بانر الصفحة الرئيسية"
        verbose_name_plural = "بانرات الصفحة الرئيسية (السلايدر)"

    def __str__(self):
        return self.title_ar

# 3. جدول متغيرات المنتج (Product Variants - زي ما كلود اقترح بالظبط)
# التيشيرت مش منتج واحد، التيشيرت (أسود - L) ده اللي بيتباع ويتخصم من المخزن
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, blank=True, null=True, verbose_name="المقاس") # S, M, L, XL
    color_ar = models.CharField(max_length=50, blank=True, null=True, verbose_name="اللون (عربي)")
    color_en = models.CharField(max_length=50, blank=True, null=True, verbose_name="اللون (إنجليزي)")
    
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="الكمية في المخزن")

    def __str__(self):
        return f"{self.product.name_en} - {self.size} - {self.color_en}"
    
# موديل السلة
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سلة رقم {self.id}"

    @property
    def total_price(self):
        # دالة بتحسب إجمالي السعر لكل اللي في السلة
        return sum(item.total_price for item in self.items.all())

# موديل عناصر السلة (التيشيرتات المختارة)
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # بنربط العنصر بالمقاس اللي الزبون اختاره من الـ Variants
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True) 
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name_ar}"

    @property
    def total_price(self):
        # سعر القطعة في الكمية
        return self.product.price * self.quantity
    
# جدول الصور المتعددة للمنتج
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/', verbose_name="الصورة الإضافية")

    def __str__(self):
        return f"صورة إضافية لـ {self.product.name_ar}"

# جدول الطلبات
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'قيد الانتظار'),
        ('Processing', 'جاري التجهيز'),
        ('Shipped', 'تم الشحن'),
        ('Delivered', 'تم التوصيل'),
        ('Cancelled', 'ملغي'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100, verbose_name="الاسم بالكامل")
    phone = models.CharField(max_length=20, verbose_name="رقم التليفون")
    address = models.TextField(verbose_name="عنوان التوصيل")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="حالة الطلب")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الإجمالي النهائي")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")

    def __str__(self):
        return f"طلب رقم {self.id} - {self.full_name}"

# جدول تفاصيل الطلب
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر وقت الشراء")

    def __str__(self):
        return f"{self.quantity} x {self.product.name_ar} (طلب {self.order.id})"
class Order(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="الاسم بالكامل")
    phone = models.CharField(max_length=20, verbose_name="رقم التليفون")
    email = models.EmailField(blank=True, null=True, verbose_name="الإيميل")
    address = models.CharField(max_length=500, verbose_name="العنوان")
    building = models.CharField(max_length=50, default="-", verbose_name="عمارة")
    floor = models.CharField(max_length=50, default="-", verbose_name="دور")
    apartment = models.CharField(max_length=50, default="-", verbose_name="شقة")
    landmark = models.CharField(max_length=255, blank=True, null=True, verbose_name="علامة مميزة")
    region = models.CharField(max_length=100, default="-", verbose_name="المحافظة")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="إجمالي الحساب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    is_completed = models.BooleanField(default=False, verbose_name="تم التوصيل؟")

    def __str__(self):
        return f"طلب رقم {self.id} - {self.full_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name_ar} (x{self.quantity})"
    