"""
Django settings for config project.
"""

from decouple import config
from pathlib import Path
from datetime import timedelta
import sentry_sdk
import dj_database_url
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
# تم تحديث الدومين ليتطابق مع رابط موقع مهاجر الحالي
CSRF_TRUSTED_ORIGINS = ['https://mohager-store-production.up.railway.app']

# Application definition
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',   # Advanced filters
    'unfold.contrib.forms',     # Custom forms
    'unfold.contrib.inlines',   # Custom inlines
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # REST API and utilities
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'django_filters',

    # Modular apps (explicit AppConfig so CommonConfig.ready() runs)
    'common.apps.CommonConfig',
    'products',
    'orders',
    'cart',
    'payments',
    'analytics',
    'users',

    # Existing apps
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

# ==========================================
# إعدادات django-unfold (لوحة التحكم الحديثة)
# ==========================================
UNFOLD = {
    'SITE_TITLE': 'مُهاجر ستور',
    'SITE_HEADER': 'مُهاجر ستور — لوحة التحكم',
    'SITE_SYMBOL': 'shopping_bag',       # Material symbol name
    'SITE_FAVICONS': [],
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': True,
    'ENVIRONMENT': 'config.settings.environment_callback',
    'COLORS': {
        'primary': {
            '50': '250 245 255',
            '100': '243 232 255',
            '200': '233 213 255',
            '300': '216 180 254',
            '400': '192 132 252',
            '500': '168 85 247',
            '600': '147 51 234',
            '700': '126 34 206',
            '800': '107 33 168',
            '900': '88 28 135',
            '950': '59 7 100',
        },
    },
    'SIDEBAR': {
        'navigation': [
            {
                'title': 'الرئيسية',
                'icon': 'dashboard',
                'items': [
                    {
                        'title': 'لوحة التحكم',
                        'icon': 'dashboard',
                        'link': '/admin/',
                    },
                ],
            },
            {
                'title': 'المتجر',
                'icon': 'store',
                'items': [
                    {
                        'title': 'المنتجات',
                        'icon': 'inventory_2',
                        'link': '/admin/store/product/',
                    },
                    {
                        'title': 'الأقسام',
                        'icon': 'category',
                        'link': '/admin/store/category/',
                    },
                    {
                        'title': 'إعدادات المتجر',
                        'icon': 'settings',
                        'link': '/admin/store/storesetting/',
                    },
                ],
            },
            {
                'title': 'الطلبات',
                'icon': 'receipt_long',
                'items': [
                    {
                        'title': 'الطلبات',
                        'icon': 'shopping_cart',
                        'link': '/admin/store/order/',
                    },
                    {
                        'title': 'السلال',
                        'icon': 'add_shopping_cart',
                        'link': '/admin/store/cart/',
                    },
                ],
            },
            {
                'title': 'المحتوى',
                'icon': 'web',
                'items': [
                    {
                        'title': 'البانرات',
                        'icon': 'view_carousel',
                        'link': '/admin/store/heroslide/',
                    },
                ],
            },
            {
                'title': 'الحسابات',
                'icon': 'people',
                'items': [
                    {
                        'title': 'المستخدمين',
                        'icon': 'person',
                        'link': '/admin/accounts/customuser/',
                    },
                ],
            },
        ],
    },
}


def environment_callback(request):
    """Show environment badge in the admin header."""
    from django.conf import settings
    if settings.DEBUG:
        return ['Development', 'warning']
    return ['Production', 'success']


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'common.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ==========================================
# إعدادات قاعدة البيانات (PostgreSQL دايماً)
# ==========================================
# دعم DATABASE_URL من Railway
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'), conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Cairo' # 🚨 التعديل السحري لتوقيت مصر
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# ==========================================
# إعدادات Cloudinary لرفع الصور أونلاين
# ==========================================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}

# إعدادات التخزين
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = '/media/'

# API Keys & Third-Party Settings
RESEND_API_KEY = config('RESEND_API_KEY', default='')
STORE_OWNER_EMAIL = config('STORE_OWNER_EMAIL', default='')

# Allauth Settings
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory' 
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_USER_DISPLAY = 'store.forms.custom_user_display'
ACCOUNT_FORMS = {
    'signup': 'store.forms.CustomSignupForm',
}


# ==========================================
# إعدادات إرسال الإيميلات (Brevo HTTP API)
# Railway بيحجب كل منافذ SMTP، فبنستخدم HTTP API بدل كده
# ==========================================
EMAIL_BACKEND = 'anymail.backends.brevo.EmailBackend'
ANYMAIL = {
    'BREVO_API_KEY': config('BREVO_API_KEY', default=''),
}
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@mohager-store.com')

# Cache Configuration
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'mohager_store',
    }
}

# Cache timeout settings
CACHE_TIMEOUT_PRODUCT_LIST = 300  # 5 minutes
CACHE_TIMEOUT_PRODUCT_DETAIL = 600  # 10 minutes
CACHE_TIMEOUT_CATEGORY = 600  # 10 minutes
CACHE_TIMEOUT_CART = 300  # 5 minutes
CACHE_TIMEOUT_HERO_SLIDES = 600  # 10 minutes
CACHE_TIMEOUT_STORE_SETTINGS = 3600  # 1 hour

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

JWT_ACCESS_MINUTES = config('JWT_ACCESS_LIFETIME_MINUTES', default=15, cast=int)
JWT_REFRESH_DAYS = config('JWT_REFRESH_LIFETIME_DAYS', default=7, cast=int)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=JWT_ACCESS_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=JWT_REFRESH_DAYS),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('JWT_SECRET_KEY', default=SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = [origin.strip() for origin in config('CORS_ALLOWED_ORIGINS', default='http://localhost:8000').split(',')]
CORS_ALLOW_CREDENTIALS = True

# ==========================================
# إعدادات المراقبة وتتبع الأخطاء (Sentry)
# ==========================================
sentry_sdk.init(
    dsn="https://1ba0ced8739c1b36b76fb859936600ac@o4511337997729792.ingest.de.sentry.io/4511338007568272",
    send_default_pii=True,
    traces_sample_rate=0.2,  # 20% من الـ requests بس عشان الأداء
)

# ==========================================
# إعدادات الأمان للـ Production
# ==========================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # سنة كاملة
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


