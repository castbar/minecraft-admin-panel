# Modelo de Usuarios y Servidores - Cada Usuario Gestiona Sus Propios Servidores

## 📋 Nuevo Enfoque

### Cambio Principal

**Antes:** Sistema de roles compartidos (UserServerRole) donde múltiples usuarios podían acceder al mismo servidor.

**Ahora:** Sistema de ownership donde cada usuario es propietario de sus propios servidores y solo él puede gestionarlos.

## 🔐 Seguridad de Datos

### Encriptación de Contraseñas RCON

Las contraseñas RCON ahora se **encriptan automáticamente** antes de guardarse en la base de datos usando **Fernet** (symmetric encryption).

**Configuración requerida:**

1. **Generar clave de encriptación:**
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Guardar esto en .env
```

2. **Agregar al `.env`:**
```bash
ENCRYPTION_KEY=tu_clave_generada_aqui
```

3. **Importante:** 
   - Esta clave DEBE estar en variables de entorno
   - Si se pierde, no se podrán desencriptar las contraseñas
   - Guardar en lugar seguro (gestor de contraseñas)

## 👤 Sistema de Usuarios

### Creación de Usuarios

**NO hay registro público.** Solo usuarios con `is_staff=True` pueden crear usuarios Django:

```
POST /api/users/create/
Body: {
    "username": "nuevo_usuario",
    "email": "usuario@ejemplo.com",
    "password": "contraseña_segura",
    "is_staff": false,  // false = usuario normal
    "is_active": true
}
```

### Permisos

- **Usuario normal (`is_staff=False`):**
  - ✅ Puede crear sus propios servidores
  - ✅ Puede gestionar solo sus servidores
  - ❌ No puede crear otros usuarios
  - ❌ No puede ver servidores de otros usuarios

- **Staff (`is_staff=True`):**
  - ✅ Todo lo anterior
  - ✅ Puede crear usuarios Django
  - ✅ Puede ver todos los servidores (si se necesita)

## 🖥️ Creación de Servidores

### Cualquier Usuario Autenticado Puede Crear Servidores

**Antes:** Solo `is_staff=True` podía crear servidores.

**Ahora:** Cualquier usuario autenticado puede crear sus propios servidores.

```
POST /api/servers/create/
Headers: Cookie: sessionid=...
Body: {
    "name": "Mi Servidor",
    "host": "panel.castbar.dev",
    "rcon_port": 25575,
    "rcon_password": "MiContraseñaSegura123!@#",
    "port": 25565
}
```

**El servidor se crea automáticamente con:**
- `owner = usuario_actual` (quien lo crea)
- Contraseña RCON encriptada automáticamente
- Solo el owner puede verlo y gestionarlo

## 🔒 Filtrado de Servidores

### Cada Usuario Solo Ve Sus Servidores

**Antes:** `GET /api/servers/` mostraba servidores según `UserServerRole`.

**Ahora:** `GET /api/servers/` muestra **solo servidores donde `owner = usuario_actual`**.

```python
# Código interno
servers = Server.objects.filter(owner=request.user, is_active=True)
```

### Verificación de Permisos

**Antes:** Se verificaba `UserServerRole` y permisos específicos.

**Ahora:** Solo se verifica que `server.owner == request.user`.

```python
# Código interno
if server.owner != request.user:
    return error_403("No eres el propietario de este servidor")
```

## 📊 Modelo de Datos

### Cambios en el Modelo Server

```python
class Server(models.Model):
    # ... campos existentes ...
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='owned_servers',
        help_text="Usuario propietario del servidor"
    )
    rcon_password = models.CharField(
        max_length=500,  # Aumentado para almacenar contraseña encriptada
        help_text="Contraseña RCON (encriptada)"
    )
    
    def get_rcon_password(self):
        """Obtener contraseña RCON desencriptada"""
        # Desencripta automáticamente
        return decrypt_password(self.rcon_password)
    
    def save(self, *args, **kwargs):
        """Encriptar contraseña antes de guardar"""
        if self.rcon_password and not is_encrypted(self.rcon_password):
            self.rcon_password = encrypt_password(self.rcon_password)
        super().save(*args, **kwargs)
```

## 🔄 Migración de Datos

### Servidores Existentes

La migración `0011_server_owner.py`:
1. Agrega campo `owner` (temporalmente nullable)
2. Asigna servidores existentes al primer superuser
3. Hace el campo requerido

**Para servidores existentes:**
- Se asignan automáticamente al primer superuser
- Puedes cambiar el owner desde Admin Django

## 🚀 Flujo de Uso

### 1. Usuario se Registra (por Admin)

```
Admin crea usuario:
POST /api/users/create/
{
    "username": "juan",
    "password": "contraseña123",
    "is_staff": false
}
```

### 2. Usuario Hace Login

```
POST /api/auth/login/
{
    "username": "juan",
    "password": "contraseña123"
}
```

### 3. Usuario Crea Su Servidor

```
POST /api/servers/create/
{
    "name": "Servidor de Juan",
    "host": "servidor-juan.castbar.dev",
    "rcon_port": 25575,
    "rcon_password": "ContraseñaSegura123!@#"
}
```

**Resultado:**
- Servidor creado con `owner = juan`
- Contraseña encriptada en BD
- Solo `juan` puede verlo y gestionarlo

### 4. Usuario Gestiona Su Servidor

```
GET /api/servers/  # Solo muestra servidores de juan
POST /api/servers/{id}/whitelist/add/  # Solo si juan es owner
```

## 🔐 Seguridad de Contraseñas

### Encriptación Automática

- **Al guardar:** La contraseña se encripta automáticamente en `save()`
- **Al leer:** Se desencripta automáticamente en `get_rcon_password()`
- **En BD:** Solo se almacena la versión encriptada

### Ejemplo:

```python
# Crear servidor
server = Server.objects.create(
    name="Mi Servidor",
    rcon_password="MiPassword123"  # Se encripta automáticamente
)

# Leer contraseña
password = server.get_rcon_password()  # "MiPassword123" (desencriptada)
# server.rcon_password contiene la versión encriptada
```

## ⚠️ Consideraciones

### Compatibilidad con Código Existente

- `UserServerRole` se mantiene en el modelo (para compatibilidad futura)
- Pero ya no se usa para verificar permisos
- Se usa solo `server.owner` para verificar acceso

### Migración de Servidores Existentes

Si tienes servidores existentes:
1. Ejecutar migración: `python manage.py migrate`
2. Los servidores se asignan al primer superuser
3. Puedes cambiar el owner desde Admin Django si es necesario

### Variables de Entorno Necesarias

```bash
# .env
ENCRYPTION_KEY=tu_clave_fernet_aqui  # OBLIGATORIO para producción
DJANGO_SECRET_KEY=tu_secret_key
```

## 📝 Resumen de Cambios

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Crear servidores** | Solo `is_staff=True` | Cualquier usuario autenticado |
| **Ver servidores** | Según `UserServerRole` | Solo servidores propios (`owner`) |
| **Gestionar servidores** | Según rol (admin/moderator/viewer) | Solo el owner |
| **Contraseñas RCON** | Texto plano | Encriptadas (Fernet) |
| **Seguridad** | Roles compartidos | Ownership privado |

## 🎯 Ventajas del Nuevo Modelo

1. ✅ **Privacidad:** Cada usuario solo ve sus servidores
2. ✅ **Seguridad:** Contraseñas encriptadas en BD
3. ✅ **Simplicidad:** No necesita gestionar roles complejos
4. ✅ **Escalabilidad:** Cada usuario puede tener N servidores
5. ✅ **Autonomía:** Usuarios gestionan sus propios recursos
