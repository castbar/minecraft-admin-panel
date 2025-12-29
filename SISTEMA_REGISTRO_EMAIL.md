# Sistema de Registro por Email - Usuarios de Minecraft

## ✅ Implementación Completada

Se ha implementado un sistema seguro donde:
1. **Admin crea usuario** (sin contraseña)
2. **Se envía email** al usuario con token
3. **Usuario establece su propia contraseña** usando el token

## Flujo de Trabajo

### 1. Admin crea usuario
```
POST /api/servers/<id>/users/create/
Body: {
    "username": "player123",
    "email": "player@example.com"
}
```

**Respuesta:**
- Crea usuario con `is_active=False`
- Genera token único (válido 24 horas)
- Envía email con link para establecer contraseña
- Retorna: `{"success": true, "message": "User created. Email sent to player@example.com"}`

### 2. Usuario recibe email
El email contiene:
- Link directo: `{SITE_URL}/api/servers/{server_id}/users/set-password/?token={token}`
- Token para copiar/pegar
- Instrucciones de uso

### 3. Usuario establece contraseña
```
POST /api/servers/<id>/users/set-password/
Body: {
    "token": "abc123...",
    "password": "password123"
}
```

**Respuesta:**
- Valida token (debe estar vigente, < 24 horas)
- Establece contraseña (hasheada con SHA256+salt)
- Activa usuario (`is_active=True`)
- Limpia token
- Retorna: `{"success": true, "message": "Password set successfully. Your account is now active."}`

## Cambios Realizados

### Modelo MinecraftUser
- ✅ `email` - EmailField (nullable para compatibilidad)
- ✅ `password_set_token` - Token único para establecer contraseña
- ✅ `password_set_token_expires` - Expiración del token (24 horas)
- ✅ `is_active` - Ahora default=False (solo True después de establecer contraseña)
- ✅ `password_hash` y `salt` - Ahora nullable (hasta que se establezca contraseña)

### Nuevos Métodos
- `generate_password_set_token()` - Genera token y expiración
- `is_password_set_token_valid(token)` - Valida token
- `has_password_set()` - Verifica si tiene contraseña

### Nuevos Endpoints
- `POST /api/servers/<id>/users/set-password/` - Público (sin auth), establece contraseña con token

### Endpoints Modificados
- `POST /api/servers/<id>/users/create/` - Ahora requiere `email`, `password` es opcional

### Templates de Email
- `templates/emails/password_set_invitation.txt` - Versión texto
- `templates/emails/password_set_invitation.html` - Versión HTML

## Configuración Requerida

### Variables de Entorno
```bash
# Email SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com  # o tu servidor SMTP
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@example.com
EMAIL_HOST_PASSWORD=tu-password-app  # Para Gmail, usar "App Password"
DEFAULT_FROM_EMAIL=noreply@example.com

# URL base para links en emails
SITE_URL=https://tu-dominio.com  # o http://localhost:8000 para desarrollo
```

### Ejemplo con Gmail
1. Activar "Verificación en 2 pasos" en tu cuenta Google
2. Generar "Contraseña de aplicación" en: https://myaccount.google.com/apppasswords
3. Usar esa contraseña en `EMAIL_HOST_PASSWORD`

## Migración

Se creó la migración:
```
server/migrations/0004_add_email_password_token_to_minecraft_user.py
```

**Aplicar migración:**
```bash
python manage.py migrate
```

## Seguridad

✅ **Contraseñas nunca vistas por admin** - El usuario las establece directamente
✅ **Tokens con expiración** - 24 horas de validez
✅ **Tokens únicos** - Generados con `secrets.token_urlsafe(32)`
✅ **Validación de token** - Verifica expiración y existencia
✅ **Contraseñas hasheadas** - SHA256 + salt único por usuario

## Casos Especiales

### Crear usuario con contraseña directa (admin)
Si necesitas crear un usuario con contraseña directamente (casos especiales):
```json
{
    "username": "player123",
    "email": "player@example.com",
    "password": "password123"  // Opcional
}
```
Si se proporciona `password`, el usuario se crea activo inmediatamente (sin email).

## Testing

Para probar sin configurar SMTP real, puedes usar:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Esto imprimirá los emails en la consola en lugar de enviarlos.

## Próximos Pasos

1. ✅ Configurar variables de entorno de email
2. ✅ Aplicar migración: `python manage.py migrate`
3. ✅ Probar creación de usuario
4. ✅ Verificar recepción de email
5. ✅ Probar establecimiento de contraseña

