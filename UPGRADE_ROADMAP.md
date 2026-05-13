# 🚀 خطة تحديث Mohager Store - من "Script" إلى "Professional Backend"

## 📊 نظرة عامة على المراحل (12 شهر)

```
المرحلة 1-3: الأساس (أسبوع 1-2)
  ├─ إعادة تنظيم الـ Apps
  ├─ إنشاء APIs
  └─ تحسين الأمان

المرحلة 4-6: الأداء والميزات (أسبوع 3-4)
  ├─ Caching
  ├─ Background Tasks
  └─ Dashboard

المرحلة 7-9: المراقبة والتحليلات (أسبوع 5-6)
  ├─ Analytics
  ├─ Logging
  └─ Monitoring

المرحلة 10-12: الإنتاج (أسبوع 7+)
  ├─ Deployment
  ├─ Performance
  └─ Scalability
```

---

## 🔧 المرحلة 1: إعادة تنظيم الـ Project Structure

### الهدف:
كل جزء من المتجر له مكان مستقل وواضح

### البنية الجديدة:
```
mohager_store/
├── core/                          # الإعدادات المشتركة
│   ├── settings.py
│   ├── urls.py
│   ├── middleware.py
│   └── constants.py
│
├── apps/
│   ├── products/                  # إدارة المنتجات
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services.py
│   │
│   ├── orders/                    # إدارة الطلبات
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services.py
│   │
│   ├── users/                     # المستخدمين والحسابات
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── authentication.py
│   │   └── services.py
│   │
│   ├── cart/                      # السلة
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── payments/                  # الدفع
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   └── gateways.py
│   │
│   ├── analytics/                 # التحليلات
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services.py
│   │
│   ├── notifications/             # الإشعارات والبريد
│   │   ├── tasks.py
│   │   ├── services.py
│   │   ├── email_templates/
│   │   └── sms_providers.py
│   │
│   └── admin_dashboard/           # لوحة التحكم
│       ├── views.py
│       ├── urls.py
│       └── templates/
│
├── common/                        # الأدوات المشتركة
│   ├── utils.py
│   ├── decorators.py
│   ├── pagination.py
│   ├── permissions.py
│   └── validators.py
│
├── tests/                         # الاختبارات
│   ├── test_products.py
│   ├── test_orders.py
│   ├── test_users.py
│   └── test_integration.py
│
├── templates/                     # Template للـ frontend
│   ├── admin_dashboard/
│   └── emails/
│
├── static/
│   ├── admin_dashboard/
│   └── css/
│
├── media/
│   ├── products/
│   └── uploads/
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── scripts/
│   ├── manage_migrations.py
│   ├── seed_data.py
│   └── health_check.py
│
├── config/                        # الإعدادات حسب البيئة
│   ├── development.env
│   ├── staging.env
│   └── production.env
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   ├── prod.txt
│   └── test.txt
│
├── docs/                          # الوثائق
│   ├── API.md
│   ├── DATABASE.md
│   ├── SECURITY.md
│   └── DEPLOYMENT.md
│
└── .github/
    └── workflows/
        ├── tests.yml
        ├── deploy.yml
        └── security.yml
```

---

## 🔐 المرحلة 2: فصل الـ Backend عن Frontend (API-First)

### الهدف:
الـ Backend يركز على:
- البيانات والعمليات
- الحماية والصحة
- الـ APIs النظيفة

### المهام:

#### 1. إضافة Django REST Framework
```bash
pip install djangorestframework
pip install django-corsheaders
pip install drf-jwt  # أو drf-spectacular
```

#### 2. إنشاء Serializers (التحويل من Model إلى JSON)
```python
# apps/products/serializers.py
from rest_framework import serializers
from .models import Product, ProductVariant

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'stock', 'price']

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name_ar', 'name_en', 'price', 'image', 'variants', 'created_at']
```

#### 3. إنشاء ViewSets (API Endpoints)
```python
# apps/products/views.py
from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    # /api/products/
    # /api/products/{id}/
    # /api/products/?search=keyword
    # /api/products/?category=electronics
```

#### 4. URLs الجديدة
```python
# apps/products/urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'', ProductViewSet)

urlpatterns = router.urls
```

#### 5. Main URLs
```python
# core/urls.py
urlpatterns = [
    path('api/v1/products/', include('apps.products.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/cart/', include('apps.cart.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
]
```

### الـ APIs التي ستنشئها:

#### المنتجات
```
GET    /api/v1/products/              # قائمة المنتجات
GET    /api/v1/products/{id}/         # تفاصيل المنتج
POST   /api/v1/products/              # إنشاء منتج (Admin فقط)
PUT    /api/v1/products/{id}/         # تحديث منتج
DELETE /api/v1/products/{id}/         # حذف منتج
```

#### الطلبات
```
GET    /api/v1/orders/                # طلباتي
POST   /api/v1/orders/                # إنشاء طلب جديد
GET    /api/v1/orders/{id}/           # تفاصيل الطلب
PUT    /api/v1/orders/{id}/           # تحديث الطلب
DELETE /api/v1/orders/{id}/           # إلغاء الطلب
```

#### المستخدمين
```
POST   /api/v1/auth/register/         # التسجيل
POST   /api/v1/auth/login/            # تسجيل الدخول
POST   /api/v1/auth/refresh/          # تجديد Token
POST   /api/v1/auth/logout/           # تسجيل الخروج
GET    /api/v1/users/profile/         # بيانات المستخدم
PUT    /api/v1/users/profile/         # تحديث البيانات
```

#### السلة
```
GET    /api/v1/cart/                  # محتويات السلة
POST   /api/v1/cart/add/              # إضافة منتج
PUT    /api/v1/cart/update/{id}/      # تحديث الكمية
DELETE /api/v1/cart/{id}/             # حذف من السلة
```

---

## 🔑 المرحلة 3: نظام الدخول المحترف

### 1. مميزات نظام الدخول
- Email verification
- Token-based (JWT)
- Rate limiting
- 2FA (اختياري)
- Social login (Google, Facebook)

### 2. التنفيذ

#### إنشاء Custom User Model
```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
```

#### نظام التوثيق بالبريد
```python
# apps/users/services.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
import secrets

class EmailVerificationService:
    @staticmethod
    def send_verification_email(user):
        token = secrets.token_urlsafe(32)
        user.verification_token = token
        user.save()
        
        context = {
            'user': user,
            'verification_url': f"https://yoursite.com/verify/?token={token}"
        }
        
        html = render_to_string('emails/verify_email.html', context)
        send_mail(
            'تحقق من بريدك الإلكتروني',
            '',
            'noreply@mohager.com',
            [user.email],
            html_message=html
        )
```

#### Authentication Views
```python
# apps/users/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
def register(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    # التحقق من صحة البيانات
    # إنشاء المستخدم
    # إرسال بريد التحقق
    
    return Response({'message': 'تم الإرسال، تحقق من بريدك'})

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    # التحقق من الفلد والباسورد
    # إرجاع Access و Refresh Tokens
    
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    })
```

---

## 🛡️ المرحلة 4: تحسين الأمان

### 1. حماية المفاتيح
```python
# settings.py
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# HTTPS فقط في الإنتاج
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

### 2. CORS (تحديد من يقدر يستخدم API)
```python
CORS_ALLOWED_ORIGINS = [
    "https://yourfrontend.com",
    "https://yourapp.com",
]

CORS_ALLOW_CREDENTIALS = True
```

### 3. Rate Limiting (منع السبام والاختراق)
```python
# requirements.txt
django-ratelimit==4.1.0

# views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m')  # 5 محاولات كل دقيقة
def login(request):
    ...

@ratelimit(key='user', rate='10/h')  # 10 محاولات كل ساعة
def send_email_verification(request):
    ...
```

### 4. Input Validation
```python
# common/validators.py
from django.core.exceptions import ValidationError

def validate_email(email):
    if not email or '@' not in email:
        raise ValidationError("بريد غير صحيح")

def validate_password(password):
    if len(password) < 8:
        raise ValidationError("الباسورد قصير جداً")
    if not any(char.isdigit() for char in password):
        raise ValidationError("الباسورد يجب أن يحتوي على أرقام")
```

### 5. SQL Injection Prevention (استخدام ORM)
```python
# ✅ آمن
products = Product.objects.filter(name__icontains=search_query)

# ❌ غير آمن (تجنب)
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(f"SELECT * FROM products WHERE name LIKE '{search_query}'")
```

### 6. CSRF Protection
```python
# settings.py
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
]

CSRF_TRUSTED_ORIGINS = ['https://trusted-domain.com']
```

### 7. Security Headers
```python
# middleware.py
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        return response
```

---

## ⚡ المرحلة 5: تحسين الأداء

### 1. Caching مع Redis
```bash
pip install redis
pip install django-redis
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

#### استخدام الـ Cache
```python
# views.py
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# Cache الصفحة 5 دقائق
@cache_page(60 * 5)
def get_products(request):
    products = Product.objects.all()
    return Response(ProductSerializer(products, many=True).data)

# Cache يدوي
def get_product_details(request, product_id):
    cache_key = f'product_{product_id}'
    product = cache.get(cache_key)
    
    if not product:
        product = Product.objects.get(id=product_id)
        cache.set(cache_key, product, 60 * 10)  # 10 دقائق
    
    return Response(ProductSerializer(product).data)
```

### 2. Database Optimization
```python
# views.py
from django.db.models import Prefetch

# بدل هذا (N+1 queries):
orders = Order.objects.all()
for order in orders:
    print(order.items.all())  # query لكل order

# استخدم هذا:
orders = Order.objects.prefetch_related('items')
```

### 3. Background Tasks مع Celery
```bash
pip install celery
pip install redis
```

```python
# apps/notifications/tasks.py
from celery import shared_task
import time

@shared_task
def send_order_confirmation_email(order_id):
    order = Order.objects.get(id=order_id)
    # إرسال بريد بدون تأخير الـ request
    order.send_email()

# استدعاء المهمة
def create_order(request):
    order = Order.objects.create(...)
    send_order_confirmation_email.delay(order.id)  # Background task
    return Response({'order_id': order.id})
```

### 4. Pagination
```python
# common/pagination.py
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# views.py
class ProductViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
```

### 5. Select خفيف من Database
```python
# views.py
class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # بدل اختيار كل الحقول، اختر اللي تحتاجه
        return Product.objects.only('id', 'name_en', 'price', 'image')
```

---

## 📊 المرحلة 6: لوحة التحكم الاحترافية

### Dashboard الجديد يحتوي على:

```python
# apps/admin_dashboard/views.py

def dashboard_overview(request):
    """الإحصائيات الأساسية"""
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    new_users = User.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    pending_orders = Order.objects.filter(
        status='pending'
    ).count()
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'new_users': new_users,
        'pending_orders': pending_orders,
    }
    
    return Response(context)

def top_products(request):
    """أكثر المنتجات مبيعًا"""
    from django.db.models import Count
    
    top_products = Product.objects.annotate(
        sales_count=Count('orderitem')
    ).order_by('-sales_count')[:10]
    
    return Response(ProductSerializer(top_products, many=True).data)

def revenue_chart(request):
    """بيانات الأرباح يومية"""
    from django.db.models import Sum
    from datetime import timedelta
    
    last_30_days = timezone.now() - timedelta(days=30)
    
    data = Order.objects.filter(
        created_at__gte=last_30_days
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(
        revenue=Sum('total_price')
    ).order_by('day')
    
    return Response(data)
```

---

## 📈 المرحلة 7: نظام التحليلات

### ما ستتابعه

```python
# apps/analytics/models.py

class ProductView(models.Model):
    """كل مرة يشوف المستخدم منتج"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

class UserEvent(models.Model):
    """الأحداث المهمة"""
    CHOICES = [
        ('login', 'تسجيل دخول'),
        ('purchase', 'شراء'),
        ('add_to_cart', 'إضافة للسلة'),
        ('search', 'بحث'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=CHOICES)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

# تسجيل الأحداث
def log_event(user, event_type, data=None):
    UserEvent.objects.create(
        user=user,
        event_type=event_type,
        data=data or {}
    )
```

### الـ Reports

```python
def sales_report(request):
    """تقرير المبيعات الشامل"""
    from django.db.models import Sum, Count, Avg
    
    orders = Order.objects.all()
    
    report = {
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(Sum('total_price'))['total_price__sum'],
        'average_order_value': orders.aggregate(Avg('total_price'))['total_price__avg'],
        'total_customers': orders.values('user').distinct().count(),
        'top_products': Product.objects.annotate(
            sales=Count('orderitem')
        ).order_by('-sales')[:10],
    }
    
    return Response(report)
```

---

## 🚀 المرحلة 8-10: الخدمات المتقدمة

### الخدمات الداخلية (Services)

كل عملية معقدة تبقى في ملف service منفصل:

```python
# apps/orders/services.py

class OrderService:
    @staticmethod
    def create_order(user, items_data, shipping_address):
        """إنشاء طلب"""
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            status='pending'
        )
        
        for item in items_data:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )
        
        # إرسال بريد
        EmailService.send_order_confirmation(order)
        
        # تسجيل الحدث
        AnalyticsService.log_purchase(user, order)
        
        return order
    
    @staticmethod
    def cancel_order(order_id):
        """إلغاء الطلب"""
        order = Order.objects.get(id=order_id)
        
        if order.status not in ['pending', 'confirmed']:
            raise ValueError("لا يمكن إلغاء هذا الطلب")
        
        order.status = 'cancelled'
        order.save()
        
        # استرجاع المخزون
        InventoryService.restore_stock(order)
        
        # إرسال بريد الإلغاء
        EmailService.send_cancellation_email(order)
        
        return order
```

---

## 🔒 المرحلة 11: Deployment والإنتاج

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: mohager_db
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  web:
    build: .
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@db:5432/mohager_db

  celery:
    build: .
    command: celery -A core worker -l info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### التوسع والمراقبة

```python
# settings.py

# Sentry (مراقبة الأخطاء)
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

---

## 📝 ملخص المتطلبات النهائية

### Dependencies الجديدة
```
djangorestframework==3.14.0
django-filter==23.5
django-cors-headers==4.3.1
django-ratelimit==4.1.0
drf-spectacular==0.27.0
djangorestframework-simplejwt==5.3.0
celery==5.3.4
redis==5.0.1
django-redis==5.4.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
sentry-sdk==1.39.1
python-decouple==3.8
```

### مراحل الترقية المقترحة
1. **الأسبوع 1**: البنية الأساسية + إعادة التنظيم
2. **الأسبوع 2**: APIs وفصل الـ Frontend
3. **الأسبوع 3**: الأمان والتوثيق
4. **الأسبوع 4**: الأداء والـ Caching
5. **الأسبوع 5-6**: Dashboard والتحليلات
6. **الأسبوع 7+**: الاختبارات والـ Deployment

---

## 🎯 النتيجة النهائية

بعد المراحل 12، سيكون لديك:

✅ نظام منظم وقابل للصيانة
✅ APIs نظيفة وآمنة
✅ نظام دخول احترافي
✅ أمان عالي المستوى
✅ أداء ممتاز
✅ لوحة تحكم احترافية
✅ نظام تحليلات شامل
✅ جاهزية للإنتاج الحقيقي
✅ قابلية التوسع والنمو

🚀 **أنت الآن جاهز للمنافسة مع المتاجر الاحترافية!**
