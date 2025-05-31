import os
from decouple import config
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oraculo',
    'user',
    'tienda',
    'finanzas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Templates de la raíz
        ],
        'APP_DIRS': True,  # Esto debe estar en True para que encuentre templates de apps
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'finanzas.context_processors.paypal_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Santiago'

USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'user.CustomUser'

# Login/Logout URLs
LOGIN_URL = 'user:login'
LOGIN_REDIRECT_URL = 'oraculo:index'
LOGOUT_REDIRECT_URL = 'oraculo:index'

# Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para producción - configurar SMTP real
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'tu-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'tu-password-de-app'
# DEFAULT_FROM_EMAIL = 'Tarotnaútica <tu-email@gmail.com>'

# ============== CONFIGURACIÓN PARA PRESERVAR IMÁGENES PNG ============== #

# Handlers de upload para preservar archivos originales
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Configuración de archivos
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB

# Configuración para preservar imágenes PNG con capas y transparencia
PILLOW_PRESERVE_FORMAT = True
PILLOW_PNG_COMPRESS_LEVEL = 0  # Sin compresión para preservar capas
PILLOW_PRESERVE_ICC_PROFILE = True
PILLOW_PRESERVE_EXIF = True

# Configuración adicional para imágenes
IMAGE_QUALITY = 100  # Máxima calidad
IMAGE_PRESERVE_TRANSPARENCY = True
IMAGE_PRESERVE_LAYERS = True

# Configuración de Pillow para no procesar automáticamente
PILLOW_DISABLE_OPTIMIZE = True
PILLOW_DISABLE_PROGRESSIVE = True



# ============== CONFIGURACIÓN PAYPAL OPTIMIZADA ============== #
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = config('PAYPAL_MODE', default='sandbox')  # 'sandbox' o 'live'
PAYPAL_WEBHOOK_ID = config('PAYPAL_WEBHOOK_ID', default='')

# URLs de PayPal - CORREGIDAS SEGÚN LA DOCUMENTACIÓN OFICIAL
if PAYPAL_MODE == 'live':
    PAYPAL_BASE_URL = 'https://api-m.paypal.com'  # CORRECTO: api-m.paypal.com
    PAYPAL_WEB_URL = 'https://www.paypal.com'
else:
    PAYPAL_BASE_URL = 'https://api-m.sandbox.paypal.com'  # CORRECTO: api-m.sandbox.paypal.com
    PAYPAL_WEB_URL = 'https://www.sandbox.paypal.com'

# Configuración de dominio
DOMAIN_URL = config('DOMAIN_URL', default='http://127.0.0.1:8000')
PAYPAL_WEBHOOK_URL = f"{DOMAIN_URL}/cart/webhook/paypal/"

# Configuración adicional para Guest Checkout
PAYPAL_GUEST_CHECKOUT = True
PAYPAL_BRAND_NAME = "Tarotnaútica"
PAYPAL_LOCALE = "es_ES"

# Logging en desarrollo
if DEBUG:
    print(f"\n🔧 === CONFIGURACIÓN PAYPAL CORREGIDA ===")
    print(f"   Mode: {PAYPAL_MODE}")
    print(f"   Base URL: {PAYPAL_BASE_URL}")
    print(f"   Client ID: {PAYPAL_CLIENT_ID[:15] if PAYPAL_CLIENT_ID else 'NOT SET'}...")
    print(f"   Secret: {'SET' if PAYPAL_CLIENT_SECRET else 'NOT SET'}")
    print(f"   Domain: {DOMAIN_URL}")
    print(f"   Webhook URL: {PAYPAL_WEBHOOK_URL}")
    print(f"   Guest Checkout: {PAYPAL_GUEST_CHECKOUT}")
    print("=" * 45)

# Verificación de configuración requerida
PAYPAL_REQUIRED_SETTINGS = [
    'PAYPAL_CLIENT_ID',
    'PAYPAL_CLIENT_SECRET',
]

missing_settings = []
for setting in PAYPAL_REQUIRED_SETTINGS:
    if not globals().get(setting):
        missing_settings.append(setting)

if missing_settings and not DEBUG:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        f"Configuración PayPal incompleta: {', '.join(missing_settings)}"
    )

# Timeout para requests PayPal
PAYPAL_TIMEOUT = 30  # aumentado de 15 a 30 segundos

# Configuración de retry
PAYPAL_MAX_RETRIES = 3
PAYPAL_RETRY_DELAY = 1  # segundos