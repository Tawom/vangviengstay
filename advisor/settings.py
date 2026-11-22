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
    'rest_framework',
    'corsheaders',
    
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
    'inquiry',
]
# Add REST Framework settings at the bottom of the file
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow anyone to access (for testing)
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

SITE_ID = 1

# ==========================================
# 3. MIDDLEWARE
# ==========================================
# Note: UpdateCacheMiddleware MUST be near the top, FetchFromCacheMiddleware MUST be near the bottom.
MIDDLEWARE = [
    'advisor.middleware.MaintenanceModeMiddleware',       
    'django.middleware.cache.UpdateCacheMiddleware',      
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
    ('lo', 'Lao'),
    ('vi', 'Tiếng Việt'),
    ('zh-hans', '中文 (简体)'),  # Simplified Chinese
    ('ko', '한국어'),  # Korean
    ('en', 'English'),
]

# Where translation files are stored
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Asia/Vientiane'
USE_I18N = True
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
LOGIN_REDIRECT_URL = 'tour_list'
LOGOUT_REDIRECT_URL = 'tour_list'

ADMIN_SITE_HEADER = "Vang Vieng Stay Administration"
ADMIN_SITE_TITLE = "Vang Vieng Stay Admin"
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'info@vangviengstay.com')  # Made environment-agnostic

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

# Email Configuration (Anymail + Resend HTTP API)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
ANYMAIL = {
    "RESEND_API_KEY": os.getenv('ANYMAIL_RESEND_API_KEY', ''),
}

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Vang Vieng Stay <onboarding@resend.dev>').strip()
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'Vang Vieng Stay <onboarding@resend.dev>').strip()
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'info@vangviengstay.com')

# Site URL
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000').strip()

# CORS Configuration (Allow Flutter Web to connect)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:51023",
    "http://127.0.0.1:51023",
]

# Optional: For local development only, you can allow all origins to avoid port changes
CORS_ALLOW_ALL_ORIGINS = True 

# ==========================================
# EMAIL CONFIGURATION (Resend)
# ==========================================
DEFAULT_FROM_EMAIL = 'Vang Vieng Stay <noreply@vangviengstay.com>'

if DEBUG:
    # ✅ DEVELOPMENT (Mac): Print emails to terminal (no real emails sent)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # 🚀 PRODUCTION (Server): Use Resend HTTP API (Bypasses DO port blocks)
    # Note: This requires the 'resend_backend.py' file we created on the server!
    EMAIL_BACKEND = 'advisor.resend_backend.ResendBackend'
    EMAIL_HOST_PASSWORD = os.getenv('RESEND_API_KEY')