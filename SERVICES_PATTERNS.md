# 🛠️ Services & Utilities Patterns

## 📋 قاعدة ذهبية:
- كل عملية معقدة تستحق service
- Services independent من views
- Reusable و testable
- Clear responsibility

---

## 📦 Services Architecture

### 1️⃣ Product Service

```python
# apps/products/services.py

from django.db.models import Q, F, Count
from django.core.cache import cache
from django.utils.text import slugify

from .models import Product, ProductVariant, Category
from apps.analytics.services import AnalyticsService

class ProductService:
    """خدمات المنتجات"""
    
    CACHE_TTL = 3600  # ساعة واحدة
    
    @staticmethod
    def get_products(category=None, search=None, sort_by=None, page=None):
        """الحصول على المنتجات مع الفلترة والبحث"""
        
        queryset = Product.objects.filter(is_active=True)
        
        if category:
            queryset = queryset.filter(category__slug=category)
        
        if search:
            queryset = queryset.filter(
                Q(name_en__icontains=search) |
                Q(name_ar__icontains=search) |
                Q(description_en__icontains=search)
            )
        
        if sort_by == 'price_asc':
            queryset = queryset.order_by('base_price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-base_price')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-views_count')
        
        return queryset.prefetch_related('variants', 'images')
    
    @staticmethod
    def get_product_detail(product_id):
        """الحصول على تفاصيل المنتج"""
        cache_key = f'product_{product_id}'
        product = cache.get(cache_key)
        
        if not product:
            product = Product.objects.prefetch_related(
                'variants',
                'images'
            ).get(id=product_id, is_active=True)
            
            cache.set(cache_key, product, ProductService.CACHE_TTL)
        
        # زيادة عدد المشاهدات
        product.views_count = F('views_count') + 1
        product.save(update_fields=['views_count'])
        
        return product
    
    @staticmethod
    def get_related_products(product_id, limit=5):
        """الحصول على منتجات ذات صلة"""
        product = Product.objects.get(id=product_id)
        
        related = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product_id)[:limit]
        
        return related
    
    @staticmethod
    def get_top_sellers(limit=10):
        """أكثر المنتجات مبيعاً"""
        cache_key = 'top_sellers'
        top_products = cache.get(cache_key)
        
        if not top_products:
            from apps.orders.models import OrderItem
            top_products = Product.objects.annotate(
                total_sales=Count('variants__orderitem')
            ).order_by('-total_sales')[:limit]
            
            cache.set(cache_key, top_products, ProductService.CACHE_TTL)
        
        return top_products
    
    @staticmethod
    def search_products(query, limit=10):
        """البحث الذكي عن المنتجات"""
        return Product.objects.filter(
            Q(name_en__icontains=query) |
            Q(name_ar__icontains=query) |
            Q(description_en__icontains=query) |
            Q(tags__icontains=query),
            is_active=True
        )[:limit]
    
    @staticmethod
    def update_stock(variant_id, quantity_change):
        """تحديث المخزون"""
        variant = ProductVariant.objects.select_for_update().get(id=variant_id)
        
        new_stock = variant.stock + quantity_change
        
        if new_stock < 0:
            raise ValueError("المخزون غير كافي")
        
        variant.stock = new_stock
        variant.save(update_fields=['stock'])
        
        # تحديث حالة التوفر
        if new_stock == 0:
            variant.is_available = False
            variant.save(update_fields=['is_available'])
        elif not variant.is_available and new_stock > 0:
            variant.is_available = True
            variant.save(update_fields=['is_available'])
        
        return variant
    
    @staticmethod
    def calculate_final_price(product, quantity, coupon=None):
        """حساب السعر النهائي"""
        base_price = product.discounted_price * quantity
        
        discount = 0
        if coupon:
            discount = coupon.calculate_discount(base_price)
        
        tax = base_price * 0.15  # 15% tax (مثال)
        
        final_price = base_price - discount + tax
        
        return {
            'base': base_price,
            'discount': discount,
            'tax': tax,
            'total': final_price
        }
```

---

### 2️⃣ Order Service

```python
# apps/orders/services.py

from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail

from .models import Order, OrderItem, OrderHistory
from apps.cart.models import Cart
from apps.products.services import ProductService
from apps.notifications.tasks import send_order_email
from apps.analytics.services import AnalyticsService

class OrderService:
    """خدمات الطلبات"""
    
    @staticmethod
    @transaction.atomic
    def create_order(user, items_data, shipping_address, billing_address=None, coupon=None):
        """إنشاء طلب جديد"""
        
        if not billing_address:
            billing_address = shipping_address
        
        # حساب الإجمالي
        subtotal = 0
        order_items = []
        
        for item in items_data:
            variant = item['variant']
            quantity = item['quantity']
            
            # التحقق من المخزون
            if variant.available_stock < quantity:
                raise ValueError(f"المخزون غير كافي: {variant.product.name_en}")
            
            price_data = ProductService.calculate_final_price(
                variant.product,
                quantity,
                coupon
            )
            
            order_items.append({
                'variant': variant,
                'quantity': quantity,
                'unit_price': variant.price,
                'total_price': price_data['base']
            })
            
            subtotal += price_data['base']
        
        # إنشاء الطلب
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax=subtotal * 0.15,
            discount=coupon.calculate_discount(subtotal) if coupon else 0,
            total=subtotal + (subtotal * 0.15),
            shipping_address=str(shipping_address),
            billing_address=str(billing_address),
            status='pending'
        )
        
        # إضافة البنود
        for item in order_items:
            OrderItem.objects.create(
                order=order,
                product_variant=item['variant'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
            
            # تحديث المخزون المحجوز
            item['variant'].reserved_stock += item['quantity']
            item['variant'].save(update_fields=['reserved_stock'])
        
        # إضافة في السجل
        OrderHistory.objects.create(
            order=order,
            status='pending',
            change_reason='طلب جديد'
        )
        
        # إرسال بريد تأكيد
        send_order_email.delay(order.id)
        
        # تسجيل في Analytics
        AnalyticsService.log_purchase(user, order)
        
        # حذف السلة
        try:
            Cart.objects.get(user=user).delete()
        except:
            pass
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order_id, reason=""):
        """إلغاء الطلب"""
        order = Order.objects.select_for_update().get(id=order_id)
        
        if order.status not in ['pending', 'confirmed']:
            raise ValueError("لا يمكن إلغاء هذا الطلب")
        
        # استرجاع المخزون
        for item in order.items.all():
            variant = item.product_variant
            variant.reserved_stock -= item.quantity
            variant.stock += item.quantity  # إرجاع المخزون
            variant.save()
        
        # تحديث حالة الطلب
        order.status = 'cancelled'
        order.save()
        
        # إضافة في السجل
        OrderHistory.objects.create(
            order=order,
            status='cancelled',
            change_reason=reason
        )
        
        return order
    
    @staticmethod
    def update_order_status(order_id, new_status, changed_by=None, reason=""):
        """تحديث حالة الطلب"""
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        
        OrderHistory.objects.create(
            order=order,
            status=new_status,
            changed_by=changed_by,
            change_reason=reason
        )
        
        # إرسال إشعار
        send_order_email.delay(order.id, event_type='status_updated')
        
        return order
    
    @staticmethod
    def get_user_orders(user, status=None):
        """الحصول على طلبات المستخدم"""
        queryset = Order.objects.filter(user=user)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at').prefetch_related('items')
```

---

### 3️⃣ User Service

```python
# apps/users/services.py

import secrets
import hashlib
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

User = get_user_model()

class UserService:
    """خدمات المستخدمين"""
    
    @staticmethod
    def create_user(email, password, username=None):
        """إنشاء مستخدم جديد"""
        
        if not username:
            username = email.split('@')[0]
        
        # التحقق من وجود البريد
        if User.objects.filter(email=email).exists():
            raise ValueError("البريد موجود بالفعل")
        
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password
        )
        
        # إرسال بريد التحقق
        UserService.send_verification_email(user)
        
        return user
    
    @staticmethod
    def send_verification_email(user):
        """إرسال بريد التحقق"""
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.save(update_fields=['email_verification_token'])
        
        context = {
            'user': user,
            'verification_url': f"https://yourdomain.com/verify/?token={token}",
            'expiry_hours': 24
        }
        
        html_message = render_to_string('emails/verify_email.html', context)
        
        send_mail(
            'تحقق من بريدك الإلكتروني',
            '',
            'noreply@mohager.com',
            [user.email],
            html_message=html_message
        )
    
    @staticmethod
    def verify_email(token):
        """التحقق من البريد"""
        try:
            user = User.objects.get(email_verification_token=token)
            
            user.email_verified = True
            user.is_active = True
            user.email_verification_token = ''
            user.save()
            
            return user
        except User.DoesNotExist:
            raise ValueError("الرابط غير صحيح أو منتهي الصلاحية")
    
    @staticmethod
    def send_password_reset_email(email):
        """إرسال بريد إعادة تعيين الباسورد"""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # لا نخبر أن البريد غير موجود (أمان)
            return
        
        token = secrets.token_urlsafe(32)
        
        # احفظ token مؤقتاً (في الإنتاج، استخدم Redis)
        cache.set(f'password_reset_{token}', user.id, 3600)  # ساعة واحدة
        
        context = {
            'user': user,
            'reset_url': f"https://yourdomain.com/reset-password/?token={token}",
            'expiry_hours': 1
        }
        
        html_message = render_to_string('emails/password_reset.html', context)
        
        send_mail(
            'إعادة تعيين الباسورد',
            '',
            'noreply@mohager.com',
            [user.email],
            html_message=html_message
        )
    
    @staticmethod
    def reset_password(token, new_password):
        """إعادة تعيين الباسورد"""
        from django.core.cache import cache
        
        user_id = cache.get(f'password_reset_{token}')
        
        if not user_id:
            raise ValueError("رابط إعادة التعيين منتهي الصلاحية")
        
        user = User.objects.get(id=user_id)
        user.set_password(new_password)
        user.save()
        
        # احذف token
        cache.delete(f'password_reset_{token}')
        
        return user
    
    @staticmethod
    def update_profile(user, data):
        """تحديث بيانات المستخدم"""
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone = data.get('phone', user.phone)
        user.date_of_birth = data.get('date_of_birth', user.date_of_birth)
        user.save()
        
        return user
    
    @staticmethod
    def get_user_statistics(user):
        """إحصائيات المستخدم"""
        from apps.orders.models import Order
        
        orders = Order.objects.filter(user=user, status='delivered')
        
        return {
            'total_orders': orders.count(),
            'total_spent': orders.aggregate(Sum('total'))['total__sum'] or 0,
            'loyalty_points': user.loyalty_points,
            'member_since': user.created_at.date(),
        }
```

---

### 4️⃣ Cart Service

```python
# apps/cart/services.py

from django.db import transaction
from .models import Cart, CartItem
from apps.products.models import ProductVariant

class CartService:
    """خدمات السلة"""
    
    @staticmethod
    def get_or_create_cart(user):
        """الحصول على أو إنشاء سلة"""
        cart, created = Cart.objects.get_or_create(user=user)
        return cart
    
    @staticmethod
    @transaction.atomic
    def add_to_cart(user, variant_id, quantity=1):
        """إضافة منتج للسلة"""
        
        cart = CartService.get_or_create_cart(user)
        variant = ProductVariant.objects.get(id=variant_id)
        
        # التحقق من المخزون
        if variant.available_stock < quantity:
            raise ValueError(f"المخزون غير كافي. المتوفر: {variant.available_stock}")
        
        # إضافة أو تحديث
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_variant=variant
        )
        
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        
        cart_item.save()
        
        return cart_item
    
    @staticmethod
    def remove_from_cart(user, variant_id):
        """حذف من السلة"""
        cart = CartService.get_or_create_cart(user)
        CartItem.objects.filter(
            cart=cart,
            product_variant_id=variant_id
        ).delete()
    
    @staticmethod
    def update_quantity(user, variant_id, quantity):
        """تحديث الكمية"""
        if quantity <= 0:
            CartService.remove_from_cart(user, variant_id)
            return
        
        cart = CartService.get_or_create_cart(user)
        
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product_variant_id=variant_id
            )
            
            # التحقق من المخزون
            variant = cart_item.product_variant
            if variant.available_stock < quantity:
                raise ValueError(f"المخزون غير كافي. المتوفر: {variant.available_stock}")
            
            cart_item.quantity = quantity
            cart_item.save()
            
            return cart_item
        except CartItem.DoesNotExist:
            raise ValueError("هذا المنتج ليس في السلة")
    
    @staticmethod
    def get_cart_summary(user):
        """ملخص السلة"""
        cart = CartService.get_or_create_cart(user)
        items = cart.items.all().prefetch_related('product_variant')
        
        summary = {
            'items_count': sum(item.quantity for item in items),
            'total_price': sum(item.total_price for item in items),
            'items': items
        }
        
        return summary
    
    @staticmethod
    def clear_cart(user):
        """تفريغ السلة"""
        try:
            cart = Cart.objects.get(user=user)
            cart.items.all().delete()
        except:
            pass
```

---

### 5️⃣ Analytics Service

```python
# apps/analytics/services.py

from django.utils import timezone
from django.db.models import Sum, Count, Avg
from .models import ProductView, UserEvent, DailySalesReport

class AnalyticsService:
    """خدمات التحليلات"""
    
    @staticmethod
    def log_product_view(product, user=None, ip_address=None, user_agent=None):
        """تسجيل مشاهدة منتج"""
        ProductView.objects.create(
            product=product,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_event(user, event_type, data=None, ip_address=None, user_agent=None):
        """تسجيل حدث"""
        UserEvent.objects.create(
            user=user,
            event_type=event_type,
            data=data or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_purchase(user, order):
        """تسجيل عملية شراء"""
        AnalyticsService.log_event(
            user=user,
            event_type='purchase',
            data={
                'order_id': order.id,
                'amount': float(order.total),
                'items_count': order.items.count()
            }
        )
    
    @staticmethod
    def get_daily_sales_report(date=None):
        """الحصول على تقرير مبيعات يومي"""
        from apps.orders.models import Order
        
        if not date:
            date = timezone.now().date()
        
        try:
            return DailySalesReport.objects.get(date=date)
        except:
            # إنشاء التقرير إذا لم يكن موجود
            orders = Order.objects.filter(
                created_at__date=date,
                status__in=['delivered', 'shipped']
            )
            
            report = DailySalesReport.objects.create(
                date=date,
                total_orders=orders.count(),
                total_revenue=orders.aggregate(Sum('total'))['total__sum'] or 0,
                total_items_sold=sum(item.quantity for order in orders for item in order.items.all()),
                unique_customers=orders.values('user').distinct().count(),
            )
            
            return report
    
    @staticmethod
    def get_sales_analytics(start_date=None, end_date=None):
        """الحصول على تحليلات شاملة"""
        from apps.orders.models import Order
        from datetime import timedelta
        
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        return {
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(Sum('total'))['total__sum'] or 0,
            'average_order_value': orders.aggregate(Avg('total'))['total__avg'] or 0,
            'unique_customers': orders.values('user').distinct().count(),
            'daily_reports': list(
                DailySalesReport.objects.filter(
                    date__range=[start_date.date(), end_date.date()]
                ).values('date', 'total_revenue', 'total_orders')
            )
        }
```

---

## 🔧 Utility Functions

### common/utils.py

```python
import hashlib
import re
from decimal import Decimal
from django.core.exceptions import ValidationError

class ValidationUtils:
    """فحوصات البيانات"""
    
    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("البريد غير صحيح")
    
    @staticmethod
    def validate_phone(phone):
        pattern = r'^\+?1?\d{9,15}$'
        if not re.match(pattern, phone.replace(' ', '')):
            raise ValidationError("رقم الهاتف غير صحيح")
    
    @staticmethod
    def validate_password_strength(password):
        if len(password) < 12:
            raise ValidationError("الباسورد قصير (12 حرف على الأقل)")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على أحرف كبيرة")
        if not re.search(r'[a-z]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على أحرف صغيرة")
        if not re.search(r'[0-9]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على أرقام")
        if not re.search(r'[!@#$%^&*]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على رموز خاصة")

class CryptUtils:
    """أدوات التشفير"""
    
    @staticmethod
    def hash_value(value):
        """تجزئة القيمة"""
        return hashlib.sha256(value.encode()).hexdigest()
    
    @staticmethod
    def mask_email(email):
        """إخفاء البريد"""
        name, domain = email.split('@')
        return f"{name[:2]}***@{domain}"
    
    @staticmethod
    def mask_phone(phone):
        """إخفاء الهاتف"""
        return f"***{phone[-4:]}"

class PricingUtils:
    """حسابات الأسعار"""
    
    @staticmethod
    def calculate_discount(price, discount_percentage):
        """حساب الخصم"""
        return Decimal(price) * (Decimal(discount_percentage) / Decimal(100))
    
    @staticmethod
    def calculate_tax(amount, tax_rate=15):
        """حساب الضريبة"""
        return Decimal(amount) * (Decimal(tax_rate) / Decimal(100))
    
    @staticmethod
    def round_price(price):
        """تقريب السعر"""
        return round(Decimal(price), 2)

class DateUtils:
    """أدوات التواريخ"""
    
    @staticmethod
    def is_expired(date, days=1):
        """التحقق من انتهاء الصلاحية"""
        from django.utils import timezone
        from datetime import timedelta
        
        return timezone.now() > date + timedelta(days=days)
    
    @staticmethod
    def days_until(date):
        """حساب الأيام المتبقية"""
        from django.utils import timezone
        
        delta = date - timezone.now().date()
        return delta.days

class StringUtils:
    """أدوات النصوص"""
    
    @staticmethod
    def truncate(text, length=50):
        """قطع النص"""
        if len(text) > length:
            return text[:length] + "..."
        return text
    
    @staticmethod
    def slugify_arabic(text):
        """تحويل النص العربي لـ slug"""
        from django.utils.text import slugify
        return slugify(text, allow_unicode=True)
```

---

## ✅ Checklist الخدمات

- [ ] كل service مستقل وـ reusable
- [ ] error handling واضح
- [ ] transactions حيث تحتاج
- [ ] caching للعمليات الثقيلة
- [ ] logging للعمليات المهمة
- [ ] unit tests لكل service
- [ ] documentation واضحة

**الآن لديك أساس احترافي! 🚀**
