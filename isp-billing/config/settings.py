import os
from pathlib import Path
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-ganti-ini-nanti')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'accounts',
    'tenants',
    'subscribers',
    'billing',
    'nas',
    'webhooks',
    'auditlog',
    'vouchers',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'radius'),
        'HOST': os.getenv('MYSQL_HOST', '192.168.38.3'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'USER': os.getenv('MYSQL_USER'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD'),
    }
}

AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'ISP Billing API',
    'DESCRIPTION': 'API multi-tenant RADIUS + billing',
    'VERSION': '1.0.0',
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    # Akses langsung ke IP publik (via nginx reverse proxy di Webserver VM,
    # port 80) untuk testing dashboard tanpa SSH tunnel. HTTP biasa, bukan
    # HTTPS -- cukup untuk testing internal, jangan dianggap setup produksi.
    "http://103.139.163.150",
]

# Billing engine (Celery + Redis) — generate invoice berkala, tandai
# overdue, auto-suspend tenant/subscriber yang telat bayar. Lihat
# billing/tasks.py. REDIS_URL sama dipakai buat broker & result backend
# karena skala masih kecil (puluhan-ratusan tenant) — pisahkan jadi dua URL
# nanti kalau volume task sudah butuh itu.
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'daily-billing-cycle': {
        'task': 'billing.tasks.run_daily_billing_cycle',
        'schedule': crontab(hour=1, minute=0),  # 01:00 WIB tiap hari
    },
}
