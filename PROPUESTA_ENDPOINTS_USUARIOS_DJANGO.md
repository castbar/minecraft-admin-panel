# Propuesta: Endpoints para Gestión de Usuarios Django y Roles

## 📋 Situación Actual

**No existen endpoints API para gestionar:**
- Usuarios Django (crear, editar, eliminar)
- Roles de usuarios en servidores (`UserServerRole`)
- Permisos y asignación de roles

**Lo que SÍ existe:**
- Modelo `UserServerRole` en la base de datos
- Sistema de permisos basado en roles (admin, moderator, viewer)
- Endpoints para usuarios de Minecraft (no usuarios Django)

## 🎯 Endpoints Propuestos

### 1. **Gestión de Usuarios Django**

#### `GET /api/users/`
Listar todos los usuarios del sistema (solo admin)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_staff": true,
      "is_active": true,
      "date_joined": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### `POST /api/users/create/`
Crear nuevo usuario Django (solo admin)

**Request:**
```json
{
  "username": "moderator1",
  "email": "mod@example.com",
  "password": "secure_password",
  "is_staff": false,
  "is_active": true
}
```

#### `GET /api/users/<user_id>/`
Obtener detalles de un usuario (solo admin)

#### `PUT /api/users/<user_id>/update/`
Actualizar usuario (solo admin)

**Request:**
```json
{
  "email": "newemail@example.com",
  "is_active": true,
  "is_staff": false
}
```

#### `DELETE /api/users/<user_id>/delete/`
Eliminar usuario (solo admin)

#### `POST /api/users/<user_id>/change-password/`
Cambiar contraseña de usuario (solo admin)

**Request:**
```json
{
  "new_password": "new_secure_password"
}
```

---

### 2. **Gestión de Roles en Servidores**

#### `GET /api/servers/<server_id>/roles/`
Listar todos los roles asignados a un servidor

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user": {
        "id": 2,
        "username": "moderator1",
        "email": "mod@example.com"
      },
      "role": "moderator",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### `POST /api/servers/<server_id>/roles/assign/`
Asignar rol a un usuario en un servidor (requiere permiso admin en el servidor)

**Request:**
```json
{
  "user_id": 2,
  "role": "moderator"
}
```

**Roles disponibles:**
- `admin` - Acceso completo
- `moderator` - Puede gestionar whitelist, ver logs, ejecutar comandos
- `viewer` - Solo lectura

#### `PUT /api/servers/<server_id>/roles/<role_id>/update/`
Actualizar rol de un usuario (requiere permiso admin)

**Request:**
```json
{
  "role": "admin"
}
```

#### `DELETE /api/servers/<server_id>/roles/<role_id>/remove/`
Remover rol de un usuario (requiere permiso admin)

#### `GET /api/users/<user_id>/roles/`
Listar todos los servidores y roles de un usuario específico

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "server": {
        "id": 1,
        "name": "Mi Servidor"
      },
      "role": "moderator",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### 3. **Permisos y Verificación**

#### `GET /api/users/me/permissions/`
Obtener permisos del usuario actual

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "admin"
    },
    "servers": [
      {
        "server_id": 1,
        "server_name": "Mi Servidor",
        "role": "admin",
        "permissions": [
          "view",
          "manage_whitelist",
          "manage_mods",
          "control_server",
          "view_logs",
          "execute_commands",
          "manage_users",
          "manage_settings"
        ]
      }
    ]
  }
}
```

---

## 🔐 Permisos Requeridos

### Para Gestión de Usuarios Django:
- Solo usuarios con `is_staff=True` pueden gestionar usuarios Django
- Los usuarios normales no pueden crear/editar otros usuarios

### Para Gestión de Roles:
- Requiere rol `admin` en el servidor específico
- Un admin puede asignar roles a otros usuarios en sus servidores
- Un moderador NO puede asignar roles (solo puede gestionar whitelist)

---

## 📝 Ejemplo de Uso

### Escenario: Crear un moderador para un servidor

1. **Admin crea usuario Django:**
```http
POST /api/users/create/
{
  "username": "moderator1",
  "email": "mod@example.com",
  "password": "secure_password",
  "is_staff": false,
  "is_active": true
}
```

2. **Admin asigna rol de moderador al servidor:**
```http
POST /api/servers/1/roles/assign/
{
  "user_id": 2,
  "role": "moderator"
}
```

3. **El moderador ahora puede:**
   - Ver el servidor en su lista
   - Gestionar whitelist
   - Ver logs
   - Ejecutar comandos permitidos
   - **NO puede:** controlar el servidor, gestionar mods, cambiar configuración

---

## 🚀 Implementación Sugerida

**Archivo:** `panel/server/views/views_users.py`

**Funciones a crear:**
- `django_users_list` - Listar usuarios
- `django_user_create` - Crear usuario
- `django_user_detail` - Detalle de usuario
- `django_user_update` - Actualizar usuario
- `django_user_delete` - Eliminar usuario
- `django_user_change_password` - Cambiar contraseña
- `server_roles_list` - Listar roles de un servidor
- `server_role_assign` - Asignar rol
- `server_role_update` - Actualizar rol
- `server_role_remove` - Remover rol
- `user_roles_list` - Listar roles de un usuario
- `user_permissions` - Obtener permisos del usuario actual

**Decoradores necesarios:**
- `@login_required` - Para todos
- `@require_http_methods` - Especificar métodos permitidos
- Verificar `is_staff` para gestión de usuarios Django
- Verificar rol `admin` para gestión de roles en servidores

---

## ✅ Beneficios

1. **Control granular:** Los admins pueden crear moderadores con permisos limitados
2. **Seguridad:** Solo admins pueden gestionar usuarios y roles
3. **Escalabilidad:** Fácil agregar nuevos roles o permisos
4. **Auditoría:** Se puede trackear quién asignó qué rol a quién

---

¿Quieres que implemente estos endpoints ahora?

