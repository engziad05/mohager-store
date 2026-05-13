# 📊 Database Models Structure

## 🏗️ القاعدة الذهبية:
- كل app له models منطقية
- Foreign Keys واضحة
- Indexes على الحقول المستخدمة
- soft delete للبيانات المهمة
- timestamps على كل جدول

---

## 📦 Apps Structure

### 1️⃣ products/models.py

```python
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    """أقسام المنتجات"""
    name_ar = models.CharField(max_length=100, verbose_name="الاسم (عربي)")
    name_en = models.CharField(max_length=100, verbose_name="الاسم (إنجليزي)")
    slug = models.SlugField(unique=True, null=True, blank=True)
    description_ar = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name_en
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)


class Product(models.Model):
    """المنتجات الأساسية"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    
    # الأسماء والأوصاف
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, null=True, blank=True)
    description_ar = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    
    # السعر والمخزون
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # تكلفة الشراء
    discount_percentage = models.FloatField(default=0)  # خصم نسبي
    
    # الصور والألوان
    image = models.ImageField(upload_to='products/')
    color_ar = models.CharField(max_length=50, blank=True)
    color_en = models.CharField(max_length=50, blank=True)
    color_code = models.CharField(max_length=7, default="#000000")  # Hex code
    
    # معلومات إضافية
    sku = models.CharField(max_length=50, unique=True)  # Stock Keeping Unit
    brand = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=500, blank=True)  # مفصول بـ comma
    
    # الحالة
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # منتج مميز
    views_count = models.PositiveIntegerField(default=0)  # عدد المشاهدات
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return self.name_en
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)
    
    @property
    def discounted_price(self):
        """السعر بعد الخصم"""
        if self.discount_percentage:
            return self.base_price * (1 - self.discount_percentage / 100)
        return self.base_price
    
    @property
    def profit_margin(self):
        """هامش الربح"""
        if self.cost_price > 0:
            return ((self.base_price - self.cost_price) / self.base_price) * 100
        return 0


class ProductImage(models.Model):
    """صور إضافية للمنتج"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.product.name_en}"


class ProductVariant(models.Model):
    """متغيرات المنتج (المقاسات والألوان)"""
    SIZE_CHOICES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('2XL', '2X Large'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    color = models.CharField(max_length=50, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)  # قد تختلف عن السعر الأساسي
    stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.PositiveIntegerField(default=0)  # المخزون المحجوز
    
    is_available = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'size', 'color']
        indexes = [
            models.Index(fields=['product', 'is_available']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return f"{self.product.name_en} - {self.size} - {self.color}"
    
    @property
    def available_stock(self):
        """المخزون المتاح للبيع"""
        return self.stock - self.reserved_stock
```

---

### 2️⃣ users/models.py

```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """مستخدم مخصص"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # التحقق والأمان
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)
    
    # المعلومات الشخصية
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True
    )
    
    # الإحصائيات
    total_purchases = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loyalty_points = models.IntegerField(default=0)
    
    # الحالة
    is_blacklisted = models.BooleanField(default=False)  # حساب محظور
    blacklist_reason = models.TextField(blank=True)
    
    # 2FA (اختياري)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.email


class UserAddress(models.Model):
    """عناوين المستخدم"""
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    
    street = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Address"
        verbose_name_plural = "User Addresses"
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.city}"


class UserDeviceToken(models.Model):
    """أجهزة المستخدم (للإشعارات)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=200)
    push_token = models.TextField(blank=True)  # للإشعارات
    device_type = models.CharField(max_length=20, choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')])
    
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name}"
```

---

### 3️⃣ orders/models.py

```python
from django.db import models
from django.contrib.auth import get_user_model
from apps.products.models import ProductVariant

User = get_user_model()

class Order(models.Model):
    """الطلبات"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    
    # الأسعار
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)  # المجموع قبل الضريبة
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # الخصم
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # العنوان
    shipping_address = models.TextField()
    billing_address = models.TextField()
    
    # الشحن
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_method = models.CharField(max_length=50, blank=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # ملاحظات
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # الدفع
    payment_method = models.CharField(
        max_length=50,
        choices=[('card', 'Credit Card'), ('bank', 'Bank Transfer'), ('cash', 'Cash on Delivery')],
        blank=True
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # الكوبون/الخصم
    coupon_code = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """البنود في الطلب"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # السعر في وقت الشراء
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        unique_together = ['order', 'product_variant']
    
    def __str__(self):
        return f"{self.product_variant.product.name_en} x {self.quantity}"


class OrderHistory(models.Model):
    """سجل التغييرات في الطلب"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"
```

---

### 4️⃣ cart/models.py

```python
from django.db import models
from django.contrib.auth import get_user_model
from apps.products.models import ProductVariant

User = get_user_model()

class Cart(models.Model):
    """السلة"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
    
    def __str__(self):
        return f"Cart of {self.user.email}"
    
    @property
    def total_items(self):
        """إجمالي عدد البنود"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        """إجمالي السعر"""
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    """البنود في السلة"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'product_variant']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.product_variant.product.name_en} x {self.quantity}"
    
    @property
    def total_price(self):
        """السعر الإجمالي لهذا البند"""
        return self.product_variant.price * self.quantity
```

---

### 5️⃣ payments/models.py

```python
from django.db import models
from django.contrib.auth import get_user_model
from apps.orders.models import Order

User = get_user_model()

class Payment(models.Model):
    """الدفعات"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway = models.CharField(max_length=50, choices=GATEWAY_CHOICES)
    
    transaction_id = models.CharField(max_length=100, unique=True)
    reference_id = models.CharField(max_length=100, blank=True)
    
    receipt = models.TextField(blank=True)  # JSON receipt
    
    attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


class Refund(models.Model):
    """الاسترجاعات (Returns)"""
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    
    refund_date = models.DateField(null=True, blank=True)
    refund_reference = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund for Order #{self.order.order_number}"
```

---

### 6️⃣ analytics/models.py

```python
from django.db import models
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category

User = get_user_model()

class ProductView(models.Model):
    """مشاهدات المنتجات"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['product', 'created_at']),
        ]


class UserEvent(models.Model):
    """أحداث المستخدم"""
    EVENT_TYPES = [
        ('login', 'Login'),
        ('register', 'Register'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('purchase', 'Purchase'),
        ('search', 'Search'),
        ('view_product', 'View Product'),
        ('wishlist', 'Add to Wishlist'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    data = models.JSONField(default=dict, blank=True)  # بيانات إضافية
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['created_at']),
        ]


class DailySalesReport(models.Model):
    """تقرير المبيعات اليومي"""
    date = models.DateField(unique=True)
    
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_items_sold = models.PositiveIntegerField(default=0)
    avg_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    unique_customers = models.PositiveIntegerField(default=0)
    new_customers = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Daily Sales Report"
        verbose_name_plural = "Daily Sales Reports"
        ordering = ['-date']
    
    def __str__(self):
        return f"Sales Report for {self.date}"
```

---

## 🔑 Key Best Practices

### ✅ DO

```python
# استخدم ForeignKey
order = models.ForeignKey(User, on_delete=models.CASCADE)

# استخدم Choices
status = models.CharField(choices=STATUS_CHOICES)

# أضف Indexes
class Meta:
    indexes = [models.Index(fields=['created_at'])]

# استخدم Auto timestamp
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)

# استخدم Properties للحسابات
@property
def total_price(self):
    return ...
```

### ❌ DON'T

```python
# لا تستخدم CharField للتمثيل
status = models.CharField()  # ❌

# لا تخزن JSON يدويًا
data = models.TextField()  # ❌ استخدم JSONField

# لا تنسى Indexes
class Meta:
    pass  # ❌

# لا تستخدم DateTime يدويًا
created_at = models.DateTimeField(default=timezone.now)  # ❌
```

---

## 🚀 الخطوات التالية

```bash
# 1. أنسخ الـ models
# 2. تشغيل migrations
python manage.py makemigrations
python manage.py migrate

# 3. اختبار الـ models
python manage.py shell
>>> from apps.products.models import Product
>>> Product.objects.create(...)
```

**تم! الآن لديك structure منظم وآمن للبيانات! 🎉**
