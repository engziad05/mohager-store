# 🔒 Security & Configuration Guide

## 🔐 ملف Environment Variables (.env)

**أنشئ ملف `.env` في جذر المشروع:**

```env
# ==========================================
# Django Settings
# ==========================================
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# ==========================================
# Database (PostgreSQL)
# ==========================================
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mohager_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432

# ==========================================
# Email Configuration (Brevo/SendinBlue)
# ==========================================
EMAIL_BACKEND=anymail.backends.brevo.EmailBackend
BREVO_API_KEY=your-brevo-api-key
DEFAULT_FROM_EMAIL=noreply@mohager.com
ADMIN_EMAIL=admin@mohager.com

# ==========================================
# Social Authentication
# ==========================================
GOOGLE_OAUTH2_KEY=your-google-oauth-key
GOOGLE_OAUTH2_SECRET=your-google-oauth-secret

# ==========================================
# Cloud Storage (Cloudinary)
# ==========================================
CLOUDINARY_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# ==========================================
# Redis (Caching & Celery)
# ==========================================
REDIS_URL=redis://localhost:6379/0

# ==========================================
# Sentry (Error Monitoring)
# ==========================================
SENTRY_DSN=your-sentry-dsn

# ==========================================
# Payment Gateway
# ==========================================
STRIPE_API_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# ==========================================
# Security
# ==========================================
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# ==========================================
# JWT Settings
# ==========================================
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# ==========================================
# Deployment
# ==========================================
ENVIRONMENT=production  # development, staging, production
LOG_LEVEL=INFO
```

**تحديث settings.py لاستخدام .env:**

```python
# settings.py

from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# قراءة من .env
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Email
EMAIL_BACKEND = config('EMAIL_BACKEND')
BREVO_API_KEY = config('BREVO_API_KEY')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# Redis
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Security
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', cast=bool)
```

---

## 🛡️ Security Headers Middleware

```python
# common/middleware/security.py

class SecurityHeadersMiddleware:
    """إضافة security headers لكل response"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # منع Clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # منع MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # منع XSS
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
```

**إضفها لـ MIDDLEWARE في settings.py:**

```python
MIDDLEWARE = [
    ...
    'common.middleware.security.SecurityHeadersMiddleware',
]
```

---

## 🔐 SQL Injection Prevention

**❌ غير آمن:**
```python
search = request.GET.get('q')
products = Product.objects.raw(f"SELECT * FROM products WHERE name LIKE '{search}%'")
```

**✅ آمن (استخدم ORM):**
```python
from django.db.models import Q

search = request.GET.get('q')
products = Product.objects.filter(
    Q(name__icontains=search) | Q(description__icontains=search)
)
```

---

## 🛡️ CSRF Protection

```python
# settings.py

CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]

CSRF_COOKIE_HTTPONLY = True
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
```

**في HTML templates:**
```html
<form method="post">
    {% csrf_token %}
    ...
</form>
```

**في API requests (JavaScript):**
```javascript
// احصل على CSRF token
const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
};

// استخدمه في requests
fetch('/api/v1/orders/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({ ... })
});
```

---

## 🔐 Authentication & Authorization

```python
# settings.py

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('JWT_SECRET_KEY', default=SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Permissions in Django Admin
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

---

## ⚙️ Logging Configuration

```python
# settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

---

## 🚨 Rate Limiting

```python
# settings.py

RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# common/decorators.py
from django_ratelimit.decorators import ratelimit

# استخدم في views
@ratelimit(key='ip', rate='10/m', method=['POST'])
def create_order(request):
    """10 طلبات كل دقيقة لكل IP"""
    ...

@ratelimit(key='user', rate='5/h', method=['POST'])
def send_email_verification(request):
    """5 محاولات كل ساعة لكل مستخدم"""
    ...
```

---

## 🔐 Password Hashing

```python
# settings.py

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # 12 حرف على الأقل
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # Custom validator
    {
        'NAME': 'common.validators.PasswordComplexityValidator',
    },
]
```

```python
# common/validators.py

from django.core.exceptions import ValidationError
import re

class PasswordComplexityValidator:
    """باسورد قوي مع أحرف وأرقام ورموز"""
    
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على أحرف صغيرة")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على أحرف كبيرة")
        
        if not re.search(r'[0-9]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على أرقام")
        
        if not re.search(r'[!@#$%^&*]', password):
            raise ValidationError("الباسورد يجب أن يحتوي على رموز خاصة (!@#$%^&*)")
    
    def get_help_text(self):
        return "الباسورد يجب أن يحتوي على أحرف كبيرة وصغيرة وأرقام ورموز"
```

---

## 🚀 Deployment Settings

```python
# settings.py

ENVIRONMENT = config('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # سنة واحدة
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Content Security
    SECURE_CONTENT_SECURITY_POLICY = {
        'DEFAULT_SRC': ("'self'",),
        'SCRIPT_SRC': ("'self'", "'unsafe-inline'"),
        'IMG_SRC': ("'self'", "data:", "https:"),
        'FONT_SRC': ("'self'",),
        'CONNECT_SRC': ("'self'",),
    }
    
    # Static files
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    
    # Sentry
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=ENVIRONMENT,
    )
```

---

## ✅ Security Checklist

قبل الـ Production:

- [ ] تغيير `SECRET_KEY` لمفتاح عشوائي قوي
- [ ] ضبط `DEBUG = False`
- [ ] تفعيل `HTTPS` و `SECURE_SSL_REDIRECT`
- [ ] تثبيت `HSTS` headers
- [ ] تغيير `ALLOWED_HOSTS`
- [ ] ضبط `CSRF_TRUSTED_ORIGINS`
- [ ] حماية Database بـ password قوي
- [ ] تفعيل Rate Limiting
- [ ] إضافة Security Headers Middleware
- [ ] تفعيل SQL prepared statements (ORM)
- [ ] إضافة Sentry للمراقبة
- [ ] تشفير الحقول الحساسة
- [ ] تفعيل 2FA (إذا لزم)
- [ ] عمل Security Audit
- [ ] تثبيت Firewall والـ DDoS protection
- [ ] عمل Regular backups

---

## 🔍 Testing Security

```python
# tests/test_security.py

from django.test import TestCase, Client
from rest_framework import status

class SecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_csrf_protection(self):
        """اختبار حماية CSRF"""
        response = self.client.post('/api/v1/orders/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_sql_injection_prevention(self):
        """منع SQL Injection"""
        response = self.client.get("/api/v1/products/?search='; DROP TABLE products;--")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_rate_limiting(self):
        """اختبار Rate Limiting"""
        for i in range(15):
            response = self.client.post('/api/v1/auth/login/', {'email': 'test@test.com', 'password': 'test'})
        
        # بعد 10 محاولات يجب أن يرفع 429 Too Many Requests
        self.assertIn(response.status_code, [429, 400])
```

---

## 📋 Checklist الأمان الشامل

### الأساسيات
- [ ] Environment variables محمية
- [ ] Secrets لا تُكتب في الكود
- [ ] Debug = False في الإنتاج
- [ ] HTTPS مفعل

### Database
- [ ] Passwords قوية
- [ ] Backups منتظمة
- [ ] لا توجد مفاتيح في الـ database
- [ ] Encryption للبيانات الحساسة

### API
- [ ] Authentication (JWT)
- [ ] Authorization/Permissions
- [ ] Rate Limiting
- [ ] Input Validation
- [ ] Error messages لا تفشي تفاصيل المشروع

### Infrastructure
- [ ] Firewall
- [ ] DDoS Protection
- [ ] SSL Certificate
- [ ] Monitoring & Logging
- [ ] Regular Updates

### Application
- [ ] No SQL Injection
- [ ] No XSS
- [ ] No CSRF
- [ ] Secure Password Storage
- [ ] 2FA (optional)

---

**الآن أنت مستعد! 🎉**
