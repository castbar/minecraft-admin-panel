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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir archivos estáticos en producción
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

# WhiteNoise para servir archivos estáticos en producción
# Usar CompressedManifestStaticFilesStorage para producción
# Esto genera archivos con hash en el nombre para cache busting
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración adicional de WhiteNoise
WHITENOISE_USE_FINDERS = True  # Permitir buscar archivos estáticos en STATICFILES_DIRS
WHITENOISE_AUTOREFRESH = True  # Recargar archivos en desarrollo

# NOTA: El frontend se sirve desde Nginx (servicio separado)
# Django solo maneja archivos estáticos del admin y panel interno
# Solo agregar STATICFILES_DIRS si el directorio existe
STATICFILES_DIRS = []
if os.path.exists(BASE_DIR / 'static'):
    STATICFILES_DIRS.append(BASE_DIR / 'static')

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
    'http://localhost:8080',  # Frontend Nginx
]
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL', 'False') == 'True'  # Solo en desarrollo
CORS_ALLOW_CREDENTIALS = True  # Permitir cookies para autenticación por sesión

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',  # Frontend Nginx
    'http://localhost:4200',  # Angular dev server
    'http://localhost:8100',  # Ionic dev server
    'http://100.77.240.103:8080',  # Servidor de producción
    'https://100.77.240.103:8080',  # Servidor de producción (HTTPS si aplica)
]

# Agregar origen desde variable de entorno si está configurado
site_url = os.environ.get('SITE_URL', '')
if site_url and site_url not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(site_url)

# Email Configuration
# Soporta múltiples nombres de variables para compatibilidad con diferentes sistemas
# Variables estándar Django: EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
# Variables alternativas: SMTP_HOST, SMTP_USER, SMTP_PASSWORD
# Variables del servidor: EMAIL_USER (para iCloud puede usarse como usuario SMTP)

# Backend: usar SMTP si está configurado, sino console para desarrollo
email_backend_env = os.environ.get('EMAIL_BACKEND') or os.environ.get('SMTP_BACKEND')
if email_backend_env:
    EMAIL_BACKEND = email_backend_env
elif os.environ.get('SMTP_HOST') or os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Host SMTP (soporta EMAIL_HOST, SMTP_HOST, o detectar desde EMAIL_USER)
smtp_host = os.environ.get('EMAIL_HOST') or os.environ.get('SMTP_HOST')
if not smtp_host:
    # Detectar host SMTP desde el email del usuario (si es iCloud)
    email_user = os.environ.get('EMAIL_USER') or os.environ.get('EMAIL_HOST_USER') or os.environ.get('SMTP_USER') or ''
    if '@icloud.com' in email_user or '@me.com' in email_user:
        smtp_host = 'smtp.mail.me.com'  # SMTP de iCloud
    elif '@gmail.com' in email_user:
        smtp_host = 'smtp.gmail.com'
    else:
        smtp_host = 'smtp.gmail.com'  # Default
EMAIL_HOST = smtp_host

# Puerto SMTP (soporta EMAIL_PORT, SMTP_PORT, o detectar desde host)
email_port = os.environ.get('EMAIL_PORT') or os.environ.get('SMTP_PORT')
if not email_port:
    # Detectar puerto según el host
    if 'mail.me.com' in EMAIL_HOST or 'icloud' in EMAIL_HOST:
        email_port = '587'  # iCloud SMTP
    else:
        email_port = '587'  # Default TLS
EMAIL_PORT = int(email_port)

# TLS/SSL (soporta EMAIL_USE_TLS, SMTP_USE_TLS, o detectar)
email_use_tls = os.environ.get('EMAIL_USE_TLS') or os.environ.get('SMTP_USE_TLS')
if not email_use_tls:
    email_use_tls = 'True'  # Default TLS
EMAIL_USE_TLS = email_use_tls == 'True'
EMAIL_USE_SSL = (os.environ.get('EMAIL_USE_SSL') or os.environ.get('SMTP_USE_SSL') or 'False') == 'True'

# Usuario SMTP (soporta EMAIL_HOST_USER, SMTP_USER, EMAIL_USER)
EMAIL_HOST_USER = (
    os.environ.get('EMAIL_HOST_USER') or 
    os.environ.get('SMTP_USER') or 
    os.environ.get('EMAIL_USER') or 
    ''
)

# Contraseña SMTP (soporta EMAIL_HOST_PASSWORD, SMTP_PASSWORD, EMAIL_PASSWORD)
EMAIL_HOST_PASSWORD = (
    os.environ.get('EMAIL_HOST_PASSWORD') or 
    os.environ.get('SMTP_PASSWORD') or 
    os.environ.get('EMAIL_PASSWORD') or 
    ''
)

# Email remitente (soporta DEFAULT_FROM_EMAIL, EMAIL_FROM_EMAIL, EMAIL_FROM, SMTP_FROM)
# Si no se especifica, usar el mismo que EMAIL_HOST_USER (requerido para algunos proveedores como iCloud)
default_from_env = (
    os.environ.get('DEFAULT_FROM_EMAIL') or 
    os.environ.get('EMAIL_FROM_EMAIL') or 
    os.environ.get('EMAIL_FROM') or 
    os.environ.get('SMTP_FROM')
)
DEFAULT_FROM_EMAIL = default_from_env or EMAIL_HOST_USER or 'noreply@minecraft-panel.local'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Nombre del remitente (opcional)
EMAIL_FROM_NAME = os.environ.get('EMAIL_FROM_NAME') or 'Minecraft Server Manager'

# URL base para links en emails (usado en templates)
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# File Upload Settings - Permitir archivos grandes (200MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024  # 200MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024  # 200MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/data/logs/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'server': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
import os
os.makedirs('/data/logs', exist_ok=True)

