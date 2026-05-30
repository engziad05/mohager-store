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
    color_ar = models.CharField(max_length=50, blank=True, null=True, verbose_name='اللون (عربي)')
    color_en = models.CharField(max_length=50, blank=True, null=True, verbose_name='اللون (إنجليزي)')
    color_code = models.CharField(
        max_length=20,
        verbose_name='كود اللون (Hex)',
        default='#111111',
    )
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


class ProductPrint(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='prints',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100, verbose_name='اسم الطبعه')
    icon = models.ImageField(upload_to='products/prints/icons/', verbose_name='صورة الزر (أيقونة)', help_text='صورة مصغرة تظهر كزر')
    main_image = models.ImageField(upload_to='products/prints/main/', verbose_name='الصورة الرئيسية للطبعه')
    is_default = models.BooleanField(default=False, verbose_name='طبعه افتراضية')

    class Meta:
        db_table = 'store_productprint'
        verbose_name = 'Product Print'
        verbose_name_plural = 'Product Prints'

    def __str__(self):
        return f'{self.product.name_en} - {self.name}'

    @property
    def in_stock(self):
        variants = self.variants.all()
        if not variants:
            return True
        return any(v.stock > 0 for v in variants)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE,
    )
    product_print = models.ForeignKey(
        ProductPrint,
        related_name='gallery_images',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='الطبعه (اختياري)',
        help_text='لو الصورة دي تابعة لطبعه معينة، اختارها من هنا.',
    )
    image = models.ImageField(
        upload_to='products/gallery/',
        verbose_name='الصورة الإضافية',
    )

    class Meta:
        db_table = 'store_productimage'

    def __str__(self):
        return f'صورة إضافية لـ {self.product.name_en}'


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='variants',
        on_delete=models.CASCADE,
    )
    product_print = models.ForeignKey(
        ProductPrint,
        related_name='variants',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='الطبعه (اختياري)',
        help_text='لو المقاس ده لطبعه معينة، اختارها من هنا.',
    )
    size = models.CharField(max_length=10, blank=True, null=True, verbose_name='المقاس')
    weight_range = models.CharField(max_length=50, blank=True, null=True, verbose_name='الوزن (من-إلى)', help_text='مثال: 70-85')
    stock = models.PositiveIntegerField(default=0, verbose_name='المخزون')

    class Meta:
        db_table = 'store_productvariant'

    def __str__(self):
        return f'{self.product.name_en} - {self.size} - {self.product.color_en}'
