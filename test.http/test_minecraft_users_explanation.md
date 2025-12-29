# Explicación: Endpoints de Usuarios de Minecraft

## ¿Qué son estos endpoints?

Estos endpoints **NO son para login directo de usuarios**. Son para **administrar usuarios de Minecraft** que se autenticarán en el servidor mediante un plugin/mod.

## Flujo completo de autenticación

### 1. Configuración del servidor
El servidor debe tener `auth_mode` configurado como:
- `'database'`: Solo autenticación por base de datos (usuarios con contraseña)
- `'both'`: Whitelist + Base de datos (puede usar cualquiera de los dos)

### 2. Crear usuarios (Admin)
```
POST /api/servers/<id>/users/create/
Body: {
    "username": "player123",
    "password": "password123"
}
```
- Crea un usuario en la base de datos
- El password se hashea con SHA256 + salt (método `set_password()`)
- Solo funciona si `auth_mode` es 'database' o 'both'

### 3. Login de jugadores (Plugin/Mod)
Cuando un jugador intenta conectarse al servidor:
1. El plugin/mod del servidor llama a:
   ```
   POST /api/servers/<id>/auth/
   Headers: X-API-Key: {api_key}
   Body: {
       "username": "player123",
       "password": "password123"
   }
   ```
2. El endpoint valida las credenciales usando `MinecraftUser.authenticate()`
3. Retorna `{"valid": true, "source": "database"}` si es correcto

### 4. Gestión de usuarios (Admin)
- `GET /api/servers/<id>/users/` - Listar usuarios
- `POST /api/servers/<id>/users/<user_id>/update/` - Actualizar contraseña o estado
- `POST /api/servers/<id>/users/<user_id>/delete/` - Eliminar usuario

## Modelo MinecraftUser

```python
class MinecraftUser:
    - server: ForeignKey al servidor
    - username: CharField (máx 16 caracteres, mín 3)
    - password_hash: Hash SHA256 + salt
    - salt: Token aleatorio para el hash
    - is_active: Boolean (puede desactivarse sin eliminar)
    - last_login: DateTime (se actualiza al autenticar)
    
    Métodos:
    - set_password(raw_password): Hashea la contraseña con salt
    - check_password(raw_password): Verifica la contraseña
    - authenticate(server, username, password): Autentica usuario
```

## Seguridad

- Las contraseñas se hashean con SHA256 + salt único por usuario
- No se almacenan contraseñas en texto plano
- Se requiere permiso `manage_users` para administrar usuarios
- El endpoint de autenticación puede requerir API key

## Nota importante

El servidor actual (cobblemon) tiene `auth_mode='whitelist'`, por lo que estos endpoints retornan error 400: "Server does not use database authentication". Para probarlos, necesitaríamos cambiar el `auth_mode` a 'database' o 'both'.

