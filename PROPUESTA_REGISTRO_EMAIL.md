# Propuesta: Sistema de Registro por Email para Usuarios de Minecraft

## Problema Actual

Actualmente, el administrador crea usuarios con contraseñas, lo cual:
- ❌ El admin ve las contraseñas (aunque estén hasheadas, las crea)
- ❌ No es seguro ni escalable
- ❌ No permite que los usuarios elijan sus propias contraseñas
- ❌ No hay verificación de identidad

## Solución Propuesta

Implementar un sistema de registro por email con verificación de token:

### Flujo Propuesto

1. **Usuario se registra** (público, sin autenticación):
   ```
   POST /api/servers/<id>/users/register/
   Body: {
       "username": "player123",
       "email": "player@example.com"
   }
   ```
   - Crea usuario con `is_active=False` y `email_verified=False`
   - Genera token de verificación único
   - Envía email con link de verificación

2. **Usuario verifica email**:
   ```
   POST /api/servers/<id>/users/verify-email/
   Body: {
       "token": "abc123..."
   }
   ```
   - Verifica el token
   - Marca `email_verified=True`
   - Retorna token temporal para establecer contraseña

3. **Usuario establece contraseña**:
   ```
   POST /api/servers/<id>/users/set-password/
   Body: {
       "token": "temp_token_from_verification",
       "password": "password123"
   }
   ```
   - Establece la contraseña
   - Activa el usuario (`is_active=True`)

### Cambios Necesarios

#### 1. Modelo MinecraftUser (agregar campos)

```python
class MinecraftUser(models.Model):
    # ... campos existentes ...
    email = models.EmailField(unique=True, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, null=True, blank=True)
    verification_token_expires = models.DateTimeField(null=True, blank=True)
    password_set_token = models.CharField(max_length=64, null=True, blank=True)
    password_set_token_expires = models.DateTimeField(null=True, blank=True)
```

#### 2. Nuevos Endpoints

- `POST /api/servers/<id>/users/register/` - Registro público (sin auth)
- `POST /api/servers/<id>/users/verify-email/` - Verificar email con token
- `POST /api/servers/<id>/users/set-password/` - Establecer contraseña después de verificación
- `POST /api/servers/<id>/users/resend-verification/` - Reenviar email de verificación

#### 3. Endpoint Admin (modificar)

- `POST /api/servers/<id>/users/create/` - Mantener para casos especiales (invitaciones, etc.)
  - Opcional: enviar email de bienvenida con link para establecer contraseña

#### 4. Configuración de Email

Necesario configurar en `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # o tu servidor SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@example.com'
EMAIL_HOST_PASSWORD = 'tu-password'
DEFAULT_FROM_EMAIL = 'Minecraft Panel <noreply@example.com>'
```

### Ventajas

✅ Usuario elige su propia contraseña (nunca vista por admin)
✅ Verificación de email (seguridad adicional)
✅ Escalable (no requiere intervención admin)
✅ Mejor experiencia de usuario
✅ Cumple mejores prácticas de seguridad

### Consideraciones

- Requiere servidor SMTP configurado
- Los tokens deben tener expiración (ej: 24 horas)
- Rate limiting para prevenir spam
- Validación de email format
- Manejo de emails duplicados

### Implementación

¿Quieres que implemente este sistema completo?

