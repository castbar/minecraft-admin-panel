# Sistema de Usuarios y Contraseñas

## 📋 Resumen

El sistema maneja **dos tipos de usuarios** con diferentes flujos de autenticación:

1. **Usuarios Django** (para el panel de administración)
2. **Usuarios Minecraft** (para jugar en el servidor)

---

## 👤 Usuarios Django (Panel de Administración)

### Creación

**Quién puede crear:** Solo usuarios con `is_staff=True`

**Endpoint:** `POST /api/users/create/`

**Proceso:**
1. El admin/staff crea el usuario desde el panel
2. Se proporciona:
   - `username` (requerido)
   - `email` (opcional)
   - `password` (requerido, mínimo 6 caracteres)
   - `is_staff` (opcional, default: false)
   - `is_active` (opcional, default: true)

3. **La contraseña se envía directamente al admin** (no se envía por email)
4. El admin debe comunicar la contraseña al usuario de forma segura

**Ejemplo:**
```json
POST /api/users/create/
{
    "username": "nuevo_usuario",
    "email": "usuario@ejemplo.com",
    "password": "ContraseñaSegura123",
    "is_staff": false,
    "is_active": true
}
```

**Respuesta:**
```json
{
    "success": true,
    "message": "User nuevo_usuario created successfully",
    "data": {
        "id": 2,
        "username": "nuevo_usuario",
        "email": "usuario@ejemplo.com",
        "is_staff": false,
        "is_active": true
    }
}
```

### ⚠️ Importante

- **NO se envía email automáticamente** con la contraseña
- El admin debe comunicar las credenciales al usuario de forma segura
- La contraseña se almacena con hash (Django maneja esto automáticamente)

---

## 🎮 Usuarios Minecraft (Jugadores del Servidor)

### Creación

**Quién puede crear:** El owner del servidor (o usuarios con permisos)

**Endpoint:** `POST /api/servers/{server_id}/users/create/`

**Proceso:**

#### Opción 1: Con Email (Recomendado)

1. El admin crea el usuario proporcionando:
   - `username` (requerido, mínimo 3 caracteres)
   - `email` (requerido)
   - `password` (opcional - si no se proporciona, se envía email)

2. **Si NO se proporciona password:**
   - Se genera un token único (válido por 24 horas)
   - Se envía un email al usuario con:
     - Link para establecer contraseña
     - Token para copiar/pegar
   - El usuario está `is_active=False` hasta que establezca su contraseña

3. **Si se proporciona password:**
   - Se establece directamente
   - El usuario queda `is_active=True` inmediatamente
   - **NO se envía email**

#### Opción 2: Sin Email (Caso especial)

- Se proporciona `password` directamente
- Usuario activo inmediatamente
- No se envía email

**Ejemplo (con email):**
```json
POST /api/servers/1/users/create/
{
    "username": "jugador123",
    "email": "jugador@ejemplo.com"
}
```

**Respuesta:**
```json
{
    "success": true,
    "message": "User jugador123 created. Email sent to jugador@ejemplo.com",
    "data": {
        "id": 1,
        "username": "jugador123",
        "email": "jugador@ejemplo.com",
        "is_active": false,
        "password_set_token": "abc123...",
        "password_set_token_expires": "2026-01-20T12:00:00Z"
    }
}
```

### Email de Invitación

**Template:** `panel/templates/emails/password_set_invitation.html` y `.txt`

**Contenido:**
- Saludo personalizado con nombre de usuario
- Nombre del servidor
- Link para establecer contraseña (válido 24 horas)
- Token alternativo para copiar/pegar
- Advertencia de expiración

**URL del link:**
```
{SITE_URL}/api/servers/{server_id}/users/set-password/?token={token}
```

**Ejemplo:**
```
http://localhost:8000/api/servers/1/users/set-password/?token=abc123...
```

### Establecer Contraseña

**Endpoint:** `POST /api/servers/{server_id}/users/set-password/`

**Body:**
```json
{
    "token": "abc123...",
    "password": "MiNuevaContraseña123"
}
```

**Proceso:**
1. Se valida el token (debe existir y no estar expirado)
2. Se establece la contraseña (se hashea con salt)
3. Se activa el usuario (`is_active=True`)
4. Se elimina el token

---

## 📧 Configuración de Email

### Variables de Entorno

```bash
# Backend de email (console para desarrollo, smtp para producción)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Servidor SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Credenciales
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_app

# Email remitente
DEFAULT_FROM_EMAIL=noreply@castbar.dev
SERVER_EMAIL=noreply@castbar.dev

# URL base para links en emails
SITE_URL=https://admin-minecraft.castbar.dev
```

### Estado Actual

**En desarrollo:**
- `EMAIL_BACKEND=console` (imprime emails en consola)
- No se envían emails reales

**En producción:**
- Debe configurarse `EMAIL_BACKEND=smtp`
- Deben configurarse las credenciales SMTP
- Debe configurarse `SITE_URL` con la URL pública

### Verificar Configuración

```python
# En Django shell
from django.conf import settings
from django.core.mail import send_mail

print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"SITE_URL: {settings.SITE_URL}")

# Probar envío
send_mail(
    'Test',
    'Test message',
    settings.DEFAULT_FROM_EMAIL,
    ['tu_email@ejemplo.com'],
    fail_silently=False,
)
```

---

## 🔐 Seguridad

### Usuarios Django

- Contraseñas hasheadas con algoritmo de Django (PBKDF2)
- No se almacenan en texto plano
- No se envían por email (el admin las comunica)

### Usuarios Minecraft

- Contraseñas hasheadas con SHA256 + salt único
- Tokens de establecimiento de contraseña:
  - Válidos por 24 horas
  - Únicos por usuario
  - Se eliminan después de usar
- Emails contienen tokens, no contraseñas

---

## 📝 Flujos Completos

### Flujo 1: Crear Usuario Django

```
1. Admin (staff) → Panel → Crear Usuario
2. Se proporciona: username, email, password
3. Usuario creado en BD
4. Admin comunica credenciales al usuario (fuera del sistema)
5. Usuario hace login con username/password
```

### Flujo 2: Crear Usuario Minecraft (con email)

```
1. Owner del servidor → Panel → Crear Usuario Minecraft
2. Se proporciona: username, email (sin password)
3. Sistema genera token único (24h)
4. Sistema envía email con link/token
5. Usuario recibe email
6. Usuario hace clic en link o copia token
7. Usuario establece su contraseña
8. Usuario activado (is_active=True)
9. Usuario puede jugar en el servidor
```

### Flujo 3: Crear Usuario Minecraft (sin email)

```
1. Owner del servidor → Panel → Crear Usuario Minecraft
2. Se proporciona: username, email, password
3. Usuario creado y activado inmediatamente
4. NO se envía email
5. Owner comunica credenciales al usuario
```

---

## ⚙️ Configuración Actual en el Servidor

Para verificar la configuración actual:

```bash
# En el servidor
cd /home/carlitos/repos/minecraft-admin-panel
cat .env | grep EMAIL
```

**Valores por defecto si no están configurados:**
- `EMAIL_BACKEND`: `console` (imprime en consola)
- `EMAIL_HOST`: `smtp.gmail.com`
- `EMAIL_PORT`: `587`
- `EMAIL_USE_TLS`: `True`
- `DEFAULT_FROM_EMAIL`: `noreply@minecraft-panel.local`
- `SITE_URL`: `http://localhost:8000`

---

## 🚨 Problemas Comunes

### Email no se envía

1. **Verificar configuración:**
   ```bash
   # Verificar variables de entorno
   docker exec minecraft-admin-panel env | grep EMAIL
   ```

2. **Verificar logs:**
   ```bash
   docker logs minecraft-admin-panel | grep -i email
   ```

3. **Probar envío manual:**
   ```python
   # En Django shell
   from django.core.mail import send_mail
   send_mail('Test', 'Test', 'from@ejemplo.com', ['to@ejemplo.com'])
   ```

### Token expirado

- Los tokens expiran después de 24 horas
- El admin debe generar un nuevo token o crear el usuario de nuevo

### Email en spam

- Verificar que `DEFAULT_FROM_EMAIL` tenga un dominio válido
- Configurar SPF/DKIM en el servidor de email
- Usar un servicio de email profesional (SendGrid, Mailgun, etc.)

---

## 📊 Resumen de Diferencias

| Aspecto | Usuarios Django | Usuarios Minecraft |
|---------|----------------|-------------------|
| **Quién crea** | Solo staff | Owner del servidor |
| **Email requerido** | No (opcional) | Sí (para envío de token) |
| **Password en creación** | Sí (requerido) | No (opcional) |
| **Email automático** | No | Sí (si no hay password) |
| **Token de activación** | No | Sí (24 horas) |
| **Hash de password** | Django (PBKDF2) | SHA256 + salt |
| **Uso** | Panel admin | Jugar en servidor |

---

## 🔧 Recomendaciones

1. **Para producción:**
   - Configurar SMTP real (Gmail, SendGrid, etc.)
   - Configurar `SITE_URL` con URL pública
   - Usar dominio propio para `DEFAULT_FROM_EMAIL`
   - Configurar SPF/DKIM

2. **Para desarrollo:**
   - Usar `EMAIL_BACKEND=console` para ver emails en logs
   - No configurar credenciales SMTP

3. **Seguridad:**
   - Nunca enviar contraseñas por email
   - Usar tokens con expiración
   - Validar emails antes de enviar
   - Usar HTTPS en producción
