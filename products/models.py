from django.db import models


class Category(models.Model):
    name_ar = models.CharField(max_length=100, verbose_name='الاسم (عربي)')
    name_en = models.CharField(max_length=100, verbose_name='الاسم (إنجليزي)')
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'store_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name_en


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
    )
    name_ar = models.CharField(max_length=200, verbose_name='اسم المنتج (عربي)')
    name_en = models.CharField(max_length=200, verbose_name='اسم المنتج (إنجليزي)')
    description_ar = models.TextField(verbose_name='الوصف (عربي)', blank=True)
    description_en = models.TextField(verbose_name='الوصف (إنجليزي)', blank=True)

    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='السعر الأساسي',
    )
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Original price before discount',
        help_text='Optional. Example: set 800 here and 580 as the base price.',
    )
    image = models.ImageField(
        upload_to='products/',
        verbose_name='صورة المنتج',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_product'

    def __str__(self):
        return self.name_en

    @property
    def has_discount(self):
        return bool(self.compare_at_price and self.compare_at_price > self.base_price)

    @property
    def discount_percent(self):
        if not self.has_discount:
            return 0
        discount = self.compare_at_price - self.base_price
        return round((discount / self.compare_at_price) * 100)


class ProductColor(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='colors',
        on_delete=models.CASCADE,
    )
    global_color = models.ForeignKey(
        'GlobalColor',
        on_delete=models.PROTECT,
        null=True,
        verbose_name='اللون الأساسي السادة (المرجع)',
        help_text='سيتم سحب مقاسات ومخزون هذا المنتج من مخزون اللون الأساسي المختار هنا.'
    )
    name_ar = models.CharField(max_length=100, verbose_name='اسم اللون للطبعة (عربي)')
    name_en = models.CharField(max_length=100, verbose_name='اسم اللون للطبعة (إنجليزي)', blank=True, null=True)
    color_code = models.CharField(max_length=20, verbose_name='كود اللون (Hex)', default='#111111')
    main_image = models.ImageField(upload_to='products/colors/main/', verbose_name='الصورة الرئيسية للون')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='سعر اللون',
        help_text='إذا تم تحديده، سيتم استخدام هذا السعر بدلاً من السعر الأساسي للمنتج.',
    )
    is_default = models.BooleanField(default=False, verbose_name='لون افتراضي')

    class Meta:
        db_table = 'store_productcolor'
        verbose_name = 'Product Color'
        verbose_name_plural = 'Product Colors'

    def __str__(self):
        return f'{self.product.name_en} - {self.name_ar}'

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE,
    )
    product_color = models.ForeignKey(
        ProductColor,
        related_name='gallery_images',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='اللون (اختياري)',
        help_text='لو الصورة دي تابعة للون معين، اختارها من هنا.',
    )
    image = models.ImageField(
        upload_to='products/gallery/',
        verbose_name='الصورة الإضافية',
    )

    class Meta:
        db_table = 'store_productimage'

    def __str__(self):
        return f'صورة إضافية لـ {self.product.name_en}'


class GlobalColor(models.Model):
    name_ar = models.CharField(max_length=100, verbose_name='اسم اللون (عربي)')
    name_en = models.CharField(max_length=100, verbose_name='اسم اللون (إنجليزي)', blank=True, null=True)
    color_code = models.CharField(max_length=20, verbose_name='كود اللون (Hex)', default='#111111')

    class Meta:
        db_table = 'store_globalcolor'
        verbose_name = 'لون أساسي سادة'
        verbose_name_plural = 'الألوان الأساسية السادة'

    def __str__(self):
        return self.name_ar


class MasterStock(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='القسم (نوع المنتج)')
    color = models.ForeignKey(GlobalColor, on_delete=models.CASCADE, verbose_name='اللون الأساسي السادة')

    class Meta:
        db_table = 'store_masterstock'
        unique_together = ('category', 'color')
        verbose_name = 'مخزون أساسي'
        verbose_name_plural = 'المخزون الأساسي (Master Stock)'

    def __str__(self):
        return f'{self.category.name_ar} - {self.color.name_ar}'


class MasterStockVariant(models.Model):
    master_stock = models.ForeignKey(MasterStock, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, verbose_name='المقاس')
    weight_range = models.CharField(max_length=50, blank=True, null=True, verbose_name='الوزن (من-إلى)', help_text='مثال: 70-85')
    stock = models.PositiveIntegerField(default=0, verbose_name='المخزون')

    class Meta:
        db_table = 'store_masterstockvariant'
        ordering = ['id']
        verbose_name = 'مقاس مخزون'
        verbose_name_plural = 'مقاسات المخزون'

    def __str__(self):
        return f'{self.master_stock} - {self.size}'
