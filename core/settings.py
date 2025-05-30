import os
from decouple import config
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-c6w5-!=b2gfcs3e5j1^==-=nr-!^)$70mvj@xz8(h7ssdo+7j^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

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

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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



# ============== CONFIGURACIÓN PAYPAL ============== #
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = config('PAYPAL_MODE', default='sandbox')  # 'sandbox' o 'live'
PAYPAL_WEBHOOK_ID = config('PAYPAL_WEBHOOK_ID', default='')

# URLs de PayPal
if PAYPAL_MODE == 'live':
    PAYPAL_BASE_URL = 'https://api.paypal.com'
else:
    PAYPAL_BASE_URL = 'https://api.sandbox.paypal.com'

# Configuración adicional para webhooks
PAYPAL_WEBHOOK_URL = f"{config('DOMAIN_URL', default='https://tarotnautica.store')}/cart/webhook/paypal/"