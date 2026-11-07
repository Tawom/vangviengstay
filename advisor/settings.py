"""
Django settings for advisor project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# ==========================================
# 1. SECURITY & ENVIRONMENT
# ==========================================
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-9o(z+=wff^exbvj+_wnc$&nlw93f#t2@a@$)tds%sz9olii03e')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(',')]

# ==========================================
# 2. APPLICATION DEFINITION
# ==========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    
    # Third-party apps
    'anymail',
    
    # Local apps
    'guesthouse',
    'tours',
    'dashboard',
    'guides',
    'motorbike',
    'buggy',
    'accounts',
    'ai_assistant',
    'analytics',
]

SITE_ID = 1

# ==========================================
# 3. MIDDLEWARE
# ==========================================
# Note: UpdateCacheMiddleware MUST be near the top, FetchFromCacheMiddleware MUST be near the bottom.
MIDDLEWARE = [
    'advisor.middleware.MaintenanceModeMiddleware',       
    'django.middleware.cache.UpdateCacheMiddleware',      
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',     
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics.middleware.AnalyticsMiddleware',           
    'django.middleware.cache.FetchFromCacheMiddleware',   
]

# Cache Middleware Settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'vangviengstay'

# ==========================================
# 4. URLS, TEMPLATES & WSGI
# ==========================================
ROOT_URLCONF = 'advisor.urls'

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

WSGI_APPLICATION = 'advisor.wsgi.application'

# ==========================================
# 5. DATABASE
# ==========================================
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

# ==========================================
# 6. PASSWORD VALIDATION
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================
# 7. INTERNATIONALIZATION
# ==========================================
LANGUAGE_CODE = 'en'  # Default language

# Available languages
LANGUAGES = [
    ('en', 'English'),
    ('lo', 'Lao'),
]

# Where translation files are stored
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Asia/Vientiane'
USE_I18N = True  # ✅ Make sure this is True
USE_L10N = True
USE_TZ = True

# ==========================================
# 8. STATIC & MEDIA FILES
# ==========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Where you keep your custom static files (CSS, JS, images)
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Where collectstatic gathers files for production (Nginx)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==========================================
# 9. AUTHENTICATION & ADMIN
# ==========================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'guesthouse_list'
LOGOUT_REDIRECT_URL = 'guesthouse_list'

ADMIN_SITE_HEADER = "Vang Vieng Stay Administration"
ADMIN_SITE_TITLE = "Vang Vieng Stay Admin"

# ==========================================
# 10. EXTERNAL SERVICES & CONFIGURATION
# ==========================================

# AI Assistant
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# MongoDB Atlas
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'vangviengstay')

# Caching Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'vangviengstay-cache',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Email Configuration (Resend)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.resend.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'resend').strip()
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '').strip()

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Vang Vieng Stay <info@vangviengstay.com>').strip()
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL).strip()
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000').strip()

# ==========================================
# 7. INTERNATIONALIZATION
# ==========================================
LANGUAGE_CODE = 'en'  # Default language

# Available languages
LANGUAGES = [
    ('en', 'English'),
    ('lo', 'Lao'),
]

# Where translation files are stored
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Asia/Vientiane'
USE_I18N = True  # ✅ Make sure this is True
USE_L10N = True
USE_TZ = True