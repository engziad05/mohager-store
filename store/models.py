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
    
    # الـ Soft Delete (بدل ما نمسح المنتج بنخليه False عشان الفواتير القديمة متضربش)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name_en

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