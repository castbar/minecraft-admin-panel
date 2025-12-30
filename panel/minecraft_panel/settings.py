"""
Django settings for minecraft_panel project.

Desarrollado por Castbar - Sistema de Gestión de Servidores Minecraft
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required. Set it in your .env file.")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']  # Solo accesible vía Tailscale

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'server',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'minecraft_panel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR.parent / 'templates'],
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

WSGI_APPLICATION = 'minecraft_panel.wsgi.application'

# Database
# Usar /data/db/db.sqlite3 para persistencia en volumen Docker
DB_PATH = os.environ.get('DB_PATH', str(BASE_DIR / 'db.sqlite3'))
# Si el directorio /data/db existe (volumen montado), usar ese
if os.path.exists('/data/db'):
    # Asegurar que el directorio existe y tiene permisos
    os.makedirs('/data/db', exist_ok=True)
    DB_PATH = '/data/db/db.sqlite3'
elif os.path.exists('/data') and os.access('/data', os.W_OK):
    # Si /data existe pero no /data/db, crear el directorio
    os.makedirs('/data/db', exist_ok=True)
    DB_PATH = '/data/db/db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_PATH,
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
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# NOTA: El frontend se sirve desde Nginx (servicio separado)
# Django solo maneja archivos estáticos del admin y panel interno
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Admin customization
ADMIN_SITE_HEADER = "Minecraft Server Manager"
ADMIN_SITE_TITLE = "Minecraft Server Manager"
ADMIN_INDEX_TITLE = "Bienvenido al Panel de Administración"

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# RCON Configuration
RCON_HOST = os.environ.get('RCON_HOST', 'localhost')
RCON_PORT = int(os.environ.get('RCON_PORT', '25575'))
RCON_PASSWORD = os.environ.get('RCON_PASSWORD', 'change-me-in-production')

# Minecraft Server Paths
MINECRAFT_DATA_PATH = os.environ.get('MINECRAFT_DATA_PATH', '/data')
MODS_PATH = os.path.join(MINECRAFT_DATA_PATH, 'mods')
WHITELIST_PATH = os.path.join(MINECRAFT_DATA_PATH, 'whitelist.json')
MODS_POOL_PATH = os.environ.get('MODS_POOL_PATH', '/data/mods_pool')

# Login URL
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS (solo para desarrollo, en producción solo Tailscale)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:4200',  # Angular dev server
    'http://localhost:8100',  # Ionic dev server
]
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL', 'False') == 'True'  # Solo en desarrollo
CORS_ALLOW_CREDENTIALS = True  # Permitir cookies para autenticación por sesión

# Email Configuration
# Por defecto usar console backend para desarrollo (imprime emails en consola)
# Para producción, configurar EMAIL_BACKEND=smtp en variables de entorno
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@minecraft-panel.local')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# URL base para links en emails (usado en templates)
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# File Upload Settings - Permitir archivos grandes (200MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024  # 200MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024  # 200MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

