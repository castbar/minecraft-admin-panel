# Configuración de Email

## 📧 Variables Configuradas

El sistema ahora soporta múltiples nombres de variables para compatibilidad:

### Variables Estándar Django
- `EMAIL_BACKEND` - Backend de email (smtp o console)
- `EMAIL_HOST` - Servidor SMTP
- `EMAIL_PORT` - Puerto SMTP
- `EMAIL_USE_TLS` - Usar TLS (True/False)
- `EMAIL_HOST_USER` - Usuario SMTP
- `EMAIL_HOST_PASSWORD` - Contraseña SMTP
- `DEFAULT_FROM_EMAIL` - Email remitente
- `EMAIL_FROM_NAME` - Nombre del remitente
- `SITE_URL` - URL base para links en emails

### Variables Alternativas Soportadas
- `SMTP_HOST` → `EMAIL_HOST`
- `SMTP_USER` → `EMAIL_HOST_USER`
- `SMTP_PASSWORD` → `EMAIL_HOST_PASSWORD`
- `EMAIL_USER` → `EMAIL_HOST_USER` (desde /etc/profile.d/environment.sh)
- `EMAIL_PASSWORD` → `EMAIL_HOST_PASSWORD` (desde /etc/profile.d/environment.sh)
- `EMAIL_FROM_EMAIL` → `DEFAULT_FROM_EMAIL`

### Detección Automática

Si no se configuran las variables, el sistema intenta detectar:
- **Host SMTP:** Detecta desde el dominio del email (iCloud → smtp.mail.me.com, Gmail → smtp.gmail.com)
- **Puerto:** 587 por defecto (TLS)
- **TLS:** True por defecto

## 🔧 Configuración Actual en el Servidor

**Archivo:** `/home/carlitos/repos/minecraft-admin-panel/.env`

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mail.me.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=itorts.7@icloud.com
EMAIL_HOST_PASSWORD=ldkc-wbqw-gait-umkb
DEFAULT_FROM_EMAIL=noreply@castbar.dev
EMAIL_FROM_NAME=Minecraft Server Manager
SITE_URL=http://100.77.240.103:8080
```

## 📝 Flujo de Usuarios y Contraseñas

### Usuarios Django (Panel)

**Crear usuario (sin password):**
```json
POST /api/users/create/
{
    "username": "nuevo_usuario",
    "email": "usuario@ejemplo.com",
    "is_staff": false
}
```

**Resultado:**
- Usuario creado (inactivo)
- Email enviado con link para establecer contraseña
- Usuario debe establecer su contraseña para activarse

**Establecer contraseña:**
```json
POST /api/users/set-password/
{
    "uid": "base64_encoded_user_id",
    "token": "token_generado",
    "password": "MiContraseña123"
}
```

**Cambiar contraseña propia:**
```json
POST /api/users/{user_id}/change-password/
{
    "current_password": "ContraseñaActual123",
    "new_password": "NuevaContraseña456"
}
```

### Usuarios Minecraft

**Crear usuario (sin password):**
```json
POST /api/servers/{server_id}/users/create/
{
    "username": "jugador123",
    "email": "jugador@ejemplo.com"
}
```

**Resultado:**
- Usuario creado (inactivo)
- Email enviado con link para establecer contraseña
- Usuario debe establecer su contraseña para activarse

**Establecer contraseña:**
```json
POST /api/servers/{server_id}/users/set-password/
{
    "token": "token_generado",
    "password": "MiContraseña123"
}
```

## ✅ Verificación

Para verificar que el email funciona:

```python
# En Django shell
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test',
    'Test message',
    settings.DEFAULT_FROM_EMAIL,
    ['tu_email@ejemplo.com'],
    fail_silently=False,
)
```

## 🔐 Seguridad

- Las contraseñas **nunca** se envían por email
- Solo se envían **tokens** con expiración (24 horas)
- Los usuarios establecen sus propias contraseñas
- Las contraseñas se hashean antes de guardar
