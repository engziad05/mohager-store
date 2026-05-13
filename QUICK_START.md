# 🎯 خطوات عملية للبدء الآن - Start Here!

## ✅ الخطوة 1: تحديث requirements.txt

أضف هذه الـ packages للـ requirements:

```
# API Framework
djangorestframework==3.14.0
django-filter==23.5
django-cors-headers==4.3.1
drf-spectacular==0.27.0
djangorestframework-simplejwt==5.3.0

# Performance
redis==5.0.1
django-redis==5.4.0
celery==5.3.4

# Security
django-ratelimit==4.1.0
cryptography==41.0.7

# Monitoring
sentry-sdk==1.39.1

# Database
psycopg2-binary==2.9.9

# Utils
python-decouple==3.8
python-slugify==8.0.1
```

**الأمر:**
```bash
pip install -r requirements.txt
```

---

## ✅ الخطوة 2: إعادة تنظيم Apps

الحالة الحالية:
```
store/
accounts/
```

الحالة المطلوبة:
```
apps/
├── products/
├── orders/
├── users/
├── cart/
├── payments/
└── analytics/
```

**الأوامر:**
```bash
# إنشاء مجلد apps
mkdir apps
cd apps

# إنشاء كل app
python manage.py startapp products
python manage.py startapp orders
python manage.py startapp users
python manage.py startapp cart
python manage.py startapp payments
python manage.py startapp analytics
python manage.py startapp common

# إرجوع
cd ..
```

---

## ✅ الخطوة 3: تحديث settings.py

إضف INSTALLED_APPS الجديد:

```python
# settings.py

INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # API Framework
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    
    # Apps الجديد
    'apps.products',
    'apps.orders',
    'apps.users',
    'apps.cart',
    'apps.payments',
    'apps.analytics',
    
    # Old apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'accounts',
    'store',
    'cloudinary_storage',
    'cloudinary',
    'anymail',
]

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://yourdomain.com",
]

CORS_ALLOW_CREDENTIALS = True

# Middleware الجديد
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # أضفها
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

---

## ✅ الخطوة 4: إنشاء أول API (المنتجات)

### 1. Serializer

```python
# apps/products/serializers.py

from rest_framework import serializers
from store.models import Product, ProductVariant, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'stock', 'price']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name_en', 'name_ar', 'description_en',
            'description_ar', 'base_price', 'image', 'images',
            'variants', 'category', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
```

### 2. Views (ViewSet)

```python
# apps/products/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from store.models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    Products API
    - GET /api/v1/products/ : كل المنتجات
    - GET /api/v1/products/{id}/ : تفاصيل المنتج
    - POST /api/v1/products/ : إنشاء منتج (Admin)
    - PUT /api/v1/products/{id}/ : تحديث
    - DELETE /api/v1/products/{id}/ : حذف
    """
    
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name_en', 'name_ar', 'description_en']
    ordering_fields = ['created_at', 'base_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        # Prefetch related tables للأداء
        queryset = queryset.prefetch_related(
            'variants',
            'images'
        )
        
        return queryset
    
    @method_decorator(cache_page(60 * 5))  # Cache 5 دقائق
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def top_sellers(self, request):
        """أكثر المنتجات مبيعاً"""
        from django.db.models import Count
        
        top_products = Product.objects.annotate(
            sales_count=Count('orderitem')
        ).order_by('-sales_count')[:10]
        
        serializer = self.get_serializer(top_products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """منتجات ذات صلة"""
        product = self.get_object()
        related = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:5]
        
        serializer = self.get_serializer(related, many=True)
        return Response(serializer.data)
```

### 3. URLs

```python
# apps/products/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 4. Main URLs

```python
# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('mohajer-secret-boss-2026/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
    
    # APIs
    path('api/v1/products/', include('apps.products.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/cart/', include('apps.cart.urls')),
    
    # Old URLs
    path('', include('store.urls')),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**جرب API:**
```bash
# Start development server
python manage.py runserver

# ثم افتح في المتصفح:
http://localhost:8000/api/docs/
http://localhost:8000/api/v1/products/
```

---

## ✅ الخطوة 5: نظام الدخول بـ JWT

### 1. Custom User (اختياري - إذا لم يكن موجود)

```python
# apps/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return self.email
```

### 2. Serializers

```python
# apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("الباسورد غير متطابق")
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['username'] = user.username
        return token
```

### 3. Views

```python
# apps/users/views.py

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_ratelimit.decorators import ratelimit

from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@ratelimit(key='ip', rate='5/m')  # 5 محاولات كل دقيقة
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {'message': 'تم التسجيل بنجاح'},
            status=status.HTTP_201_CREATED
        )
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
def logout(request):
    """تسجيل الخروج"""
    return Response(
        {'message': 'تم تسجيل الخروج بنجاح'},
        status=status.HTTP_200_OK
    )
```

### 4. URLs

```python
# apps/users/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    register,
    logout
)

urlpatterns = [
    path('auth/register/', register, name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout, name='logout'),
]
```

**جرب:**
```bash
# تسجيل
curl -X POST http://localhost:8000/api/v1/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"pass1234","password2":"pass1234"}'

# تسجيل دخول
curl -X POST http://localhost:8000/api/v1/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass1234"}'
```

---

## ✅ الخطوة 6: Permissions و Authentication

```python
# common/permissions.py

from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """Admin يقدر يعدل، الباقي يقدر يقرأ فقط"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    """المستخدم اللي عمل الطلب أو Admin"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user
```

### استخدام Permissions في ViewSet

```python
# apps/orders/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsOwnerOrAdmin

from .serializers import OrderSerializer
from store.models import Order

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        # كل مستخدم يشوف طلباته فقط
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # الحفظ ببيانات المستخدم الحالي
        serializer.save(user=self.request.user)
```

---

## ✅ الخطوة 7: Error Handling والـ Logging

```python
# common/exceptions.py

from rest_framework.exceptions import APIException
from rest_framework import status

class CustomAPIException(APIException):
    default_detail = 'حدث خطأ في الخادم'
    default_code = 'error'

class OrderNotFound(CustomAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'الطلب غير موجود'
    default_code = 'order_not_found'

class InsufficientStock(CustomAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'المخزون غير كافي'
    default_code = 'insufficient_stock'
```

### استخدام Exception Handlers

```python
# common/exception_handlers.py

from rest_framework.views import exception_handler
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    # Log الخطأ
    logger.error(f"API Error: {exc}", extra={
        'view': context.get('view'),
        'request': context.get('request')
    })
    
    return response

# settings.py
REST_FRAMEWORK = {
    ...
    'EXCEPTION_HANDLER': 'common.exception_handlers.custom_exception_handler'
}
```

---

## ✅ الخطوة 8: Testing

```python
# tests/test_products.py

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from store.models import Product, Category

class ProductAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name_en="Electronics",
            name_ar="إلكترونيات",
            slug="electronics"
        )
        self.product = Product.objects.create(
            category=self.category,
            name_en="Test Product",
            name_ar="منتج اختبار",
            base_price=99.99
        )
    
    def test_get_products_list(self):
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_product_detail(self):
        response = self.client.get(f'/api/v1/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name_en'], 'Test Product')
```

**تشغيل الاختبارات:**
```bash
python manage.py test tests/
# أو
pytest
```

---

## 🎯 الخطوات التالية الآن

1. ✅ **أولاً**: حدّث `requirements.txt` وركب الـ packages
2. ✅ **ثانياً**: أنشئ مجلد `apps/` بـ sub-apps
3. ✅ **ثالثاً**: حدّث `settings.py`
4. ✅ **رابعاً**: أنشئ أول API للمنتجات
5. ✅ **خامساً**: أضف نظام الدخول
6. ✅ **سادساً**: أضف الصلاحيات والـ permissions
7. ✅ **سابعاً**: أضف error handling
8. ✅ **ثامناً**: اكتب الاختبارات

**ثم بعدين:**
- أتمت باقي APIs
- أضف Caching
- أضف Background Tasks
- أنشئ Dashboard
- أضف Analytics
- Deploy!

---

## 📚 الموارد المهمة

- Django REST Framework: https://www.django-rest-framework.org/
- JWT Token: https://django-rest-framework-simplejwt.readthedocs.io/
- Celery: https://docs.celeryproject.io/
- Redis: https://redis.io/documentation/
- DRF Spectacular: https://drf-spectacular.readthedocs.io/
