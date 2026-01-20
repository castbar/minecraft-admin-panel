# Acceso a Paneles - Usuarios y Permisos

## 📋 Resumen

El sistema tiene **dos paneles diferentes**:

1. **Panel Django Admin** (`/admin/`) - Solo para staff
2. **Panel Minecraft Frontend** (`/`) - Para todos los usuarios autenticados

---

## 🔐 Panel Django Admin (`/admin/`)

### Acceso

**Solo usuarios con `is_staff=True` pueden acceder.**

- **URL:** `http://servidor:8080/admin/`
- **Requisito:** Usuario Django con `is_staff=True`
- **Uso:** Administración avanzada del sistema

### Qué se puede hacer en el Admin

- Ver y editar todos los modelos (Server, User, MinecraftUser, etc.)
- Gestión completa de la base de datos
- Configuración avanzada
- Ver logs de seguridad
- Gestionar backups

### Restricción

Django admin **automáticamente** verifica `is_staff=True` antes de permitir acceso. Si un usuario sin `is_staff` intenta acceder, Django lo redirige al login o muestra error 403.

---

## 🎮 Panel Minecraft Frontend (`/`)

### Acceso

**Todos los usuarios autenticados pueden acceder.**

- **URL:** `http://servidor:8080/`
- **Requisito:** Usuario Django autenticado (cualquier usuario)
- **Uso:** Gestión de servidores Minecraft

### Qué se puede hacer en el Frontend

- Ver sus propios servidores (solo los que es owner)
- Gestionar whitelist
- Ver logs
- Controlar servidor (start/stop/restart)
- Gestionar mods
- Ver jugadores
- Crear backups
- Configurar servidor

### Restricción

- Solo ve sus propios servidores (`owner = usuario`)
- Solo puede gestionar sus propios servidores
- No puede crear usuarios Django
- No puede acceder al admin de Django

---

## 🔄 Flujo de Autenticación

### Login

**Endpoint:** `POST /api/auth/login/`

```json
{
    "username": "usuario",
    "password": "contraseña"
}
```

**Proceso:**
1. Usuario se autentica con credenciales Django
2. Si es válido, se crea sesión
3. Se retornan los servidores del usuario (solo los que es owner)
4. Usuario accede al frontend

**Respuesta:**
```json
{
    "success": true,
    "authenticated": true,
    "user": {
        "id": 1,
        "username": "usuario",
        "is_staff": false
    },
    "servers": [
        {
            "id": 1,
            "name": "Mi Servidor",
            "host": "servidor.example.com",
            "role": "owner"
        }
    ]
}
```

### Verificación de Acceso

**Endpoint:** `GET /api/auth/check/`

Verifica si el usuario está autenticado y retorna sus servidores.

---

## 👥 Tipos de Usuarios

### Usuario Normal (`is_staff=False`)

**Puede:**
- ✅ Acceder al frontend (`/`) - Panel de Minecraft
- ✅ Ver sus propios servidores
- ✅ Gestionar sus servidores
- ✅ Crear nuevos servidores
- ✅ Cambiar su propia contraseña

**NO puede:**
- ❌ Acceder al admin Django (`/admin/`) - **Bloqueado automáticamente por Django**
- ❌ Crear usuarios Django
- ❌ Ver servidores de otros usuarios
- ❌ Gestionar usuarios del sistema

### Usuario Staff (`is_staff=True`)

**Puede:**
- ✅ Todo lo de usuario normal
- ✅ Acceder al admin Django (`/admin/`)
- ✅ Crear usuarios Django
- ✅ Ver todos los servidores (desde admin)
- ✅ Gestionar usuarios del sistema

---

## 🚫 Restricciones de Acceso

### Admin Django

Django **automáticamente** restringe el acceso:

```python
# Django admin verifica is_staff antes de permitir acceso
# Si el usuario no es staff, lo redirige al login o muestra 403
# Esta verificación es automática y no se puede desactivar
```

**Verificación:**
- Django admin verifica `request.user.is_staff`
- Si `False`, muestra error 403 o redirige al login
- No se puede desactivar esta verificación

**Comportamiento:**
- Usuario normal intenta acceder a `/admin/` → Django muestra login
- Si hace login pero no es staff → Error 403 "You don't have permission"
- Solo usuarios con `is_staff=True` pueden acceder

### Frontend

El frontend verifica ownership:

```python
# Solo servidores donde owner = usuario actual
servers = Server.objects.filter(owner=request.user, is_active=True)
```

**Verificación:**
- Cada endpoint verifica `server.owner == request.user`
- Si no es owner, retorna 403
- No puede ver ni gestionar servidores de otros

---

## 📊 Comparación de Paneles

| Característica | Admin Django | Frontend Minecraft |
|----------------|--------------|-------------------|
| **URL** | `/admin/` | `/` |
| **Acceso** | Solo `is_staff=True` | Todos autenticados |
| **Ver servidores** | Todos | Solo propios |
| **Crear servidores** | Sí | Sí (solo propios) |
| **Gestionar usuarios** | Sí | No |
| **Ver logs sistema** | Sí | No |
| **Configuración avanzada** | Sí | Limitada |
| **Interfaz** | Django admin | Ionic/Angular |

---

## ✅ Confirmación

**Usuarios normales (`is_staff=False`):**
- ✅ Acceden al frontend (`/`) - Panel de Minecraft
- ✅ Gestionan sus propios servidores
- ❌ **NO pueden acceder al admin Django (`/admin/`)** - Bloqueado por Django

**Usuarios staff (`is_staff=True`):**
- ✅ Acceden al frontend (`/`)
- ✅ Acceden al admin Django (`/admin/`)
- ✅ Pueden gestionar todo el sistema

**Respuesta:** Correcto, los usuarios normales **NO pueden acceder al panel de Django admin**, solo al panel de Minecraft (frontend). Django admin requiere `is_staff=True` y esta verificación es automática e inalterable.
