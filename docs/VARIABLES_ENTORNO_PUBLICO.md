# Variables de Entorno para Despliegue Público

## 📋 Variables Necesarias

Agregar estas variables al archivo `.env` del proyecto para el despliegue público:

```bash
# ============================================
# Configuración de Dominio Público
# ============================================

# Dominios permitidos (separados por comas)
ALLOWED_HOSTS=admin-minecraft.castbar.dev,100.77.240.103,localhost,127.0.0.1

# Orígenes CORS permitidos (separados por comas)
CORS_ALLOWED_ORIGINS=https://admin-minecraft.castbar.dev,http://localhost:8080,http://localhost:4200

# Orígenes confiables para CSRF (separados por comas)
CSRF_TRUSTED_ORIGINS=https://admin-minecraft.castbar.dev,http://localhost:8080

# URL base del sitio (para emails y links)
SITE_URL=https://admin-minecraft.castbar.dev

# ============================================
# Configuración Existente (mantener)
# ============================================

# Django Secret Key (ya configurado)
DJANGO_SECRET_KEY=tu_secret_key_aqui

# Debug (desactivar en producción)
DEBUG=False

# Base de datos (ya configurado)
# DB_PATH=/data/db/db.sqlite3

# ============================================
# Configuración Opcional
# ============================================

# Permitir todos los orígenes CORS (solo desarrollo)
# CORS_ALLOW_ALL=False

# Email (si quieres notificaciones)
# EMAIL_BACKEND=smtp
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=tu_email@gmail.com
# EMAIL_HOST_PASSWORD=tu_password
```

## 🔧 Aplicar Cambios

Después de actualizar el `.env`:

```bash
# Reiniciar contenedores
docker compose restart minecraft-admin-panel

# Verificar logs
docker logs minecraft-admin-panel --tail 50
```

## ✅ Verificación

1. Acceder a: `https://admin-minecraft.castbar.dev`
2. Verificar que no hay errores de CORS o CSRF
3. Probar login y funcionalidades
