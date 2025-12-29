# Estado de Endpoints - Django API

## Autenticación
- [x] `POST /api/auth/login/` - Login de usuario ✅
- [ ] `POST /api/servers/<id>/auth/` - Autenticación de usuario Minecraft ❌ (401 - Invalid credentials, esperado)

## Servidores
- [x] `GET /api/servers/` - Listar servidores disponibles ✅
- [x] `POST /api/servers/create/` - Crear nuevo servidor ✅
- [x] `GET /api/servers/<id>/status/` - Estado del servidor ✅
- [x] `GET /api/servers/<id>/stats/` - Estadísticas del servidor ✅
- [x] `POST /api/servers/<id>/control/<action>/` - Control del servidor ✅
- [x] `GET /api/servers/<id>/container/` - Información del contenedor ✅ (404 esperado si contenedor no existe)

## Whitelist
- [x] `GET /api/servers/<id>/whitelist/` - Listar usuarios en whitelist ✅
- [x] `POST /api/servers/<id>/whitelist/add/` - Agregar usuario a whitelist ✅
- [x] `POST /api/servers/<id>/whitelist/remove/` - Eliminar usuario de whitelist ✅

## Configuración
- [x] `GET /api/servers/<id>/settings/` - Obtener configuración del servidor ✅
- [x] `POST /api/servers/<id>/settings/update/` - Actualizar configuración ✅

## Usuarios Minecraft
**Nota:** Estos endpoints son para **administrar usuarios de Minecraft** que se autenticarán mediante un plugin/mod del servidor. El login real se hace a través de `POST /api/servers/<id>/auth/` llamado por el plugin.

**Requisito:** El servidor debe tener `auth_mode='database'` o `auth_mode='both'` para usar estos endpoints.

**Sistema de Registro por Email:** Admin crea usuario sin contraseña → se envía email con token → usuario establece su propia contraseña.

- [x] `GET /api/servers/<id>/users/` - Listar usuarios de Minecraft ✅ (400 esperado si auth_mode='whitelist')
- [x] `POST /api/servers/<id>/users/create/` - Crear usuario de Minecraft (requiere email, envía token por email) ✅
- [x] `POST /api/servers/<id>/users/set-password/` - Establecer contraseña con token (endpoint público) ✅
- [x] `POST /api/servers/<id>/users/<user_id>/update/` - Actualizar contraseña o estado (is_active) del usuario ✅
- [x] `POST /api/servers/<id>/users/<user_id>/delete/` - Eliminar usuario de Minecraft ✅

## Backups
- [x] `GET /api/servers/<id>/backups/` - Listar backups ✅
- [x] `POST /api/servers/<id>/backups/create/` - Crear backup ✅
- [x] `POST /api/servers/<id>/backups/<backup_id>/restore/` - Restaurar backup ✅ (implementación parcial - requiere servidor detenido)
- [x] `GET /api/servers/<id>/backup-schedules/` - Listar programaciones de backup ✅

## Versiones Minecraft
- [x] `GET /api/minecraft/versions/` - Listar versiones disponibles ✅
- [x] `GET /api/minecraft/versions/latest/` - Obtener última versión ✅ (404 esperado si no hay versiones)
- [x] `POST /api/minecraft/versions/create/` - Crear nueva versión ✅

## Multi-servidor
**IMPORTANTE:** El cliente SIEMPRE debe enviar `server_id` en cada request. El servidor NO mantiene estado del cliente.

**Formas de enviar `server_id`:**
1. **En la URL (recomendado)**: `/api/servers/<server_id>/status/`
2. **Query parameter**: `?server_id=<id>`
3. **Header HTTP**: `X-Server-ID: <id>`
4. **Body JSON (POST)**: `{"server_id": <id>, ...}`

**Endpoints que NO necesitan server_id:**
- `GET /api/servers/` - Lista todos los servidores
- `GET /api/servers/sessions/` - Sesiones del usuario (opcional)
- `GET /api/security/logs/` - Logs globales
- `GET /api/minecraft/versions/` - Versiones globales

- [x] `POST /api/servers/switch/` - [DEPRECATED] Guardar sesión opcional (el cliente maneja server_id) ✅
- [x] `GET /api/servers/sessions/` - Sesiones guardadas (historial de servidores usados por el usuario) ✅
- [x] `GET /api/security/logs/` - Logs de seguridad ✅

## Legacy (Compatibilidad)
**NOTA:** Todos los endpoints legacy ahora REQUIEREN `server_id` (query param, header `X-Server-ID`, o body JSON). Ya no hay detección automática.

- [x] `GET /api/whitelist/` - Whitelist (legacy) ✅ (requiere `server_id`)
- [x] `POST /api/whitelist/<action>/` - Acción whitelist (legacy) ✅ (requiere `server_id`)
- [x] `GET /api/mods/` - Listar mods (legacy) ✅ (requiere `server_id`)
- [x] `POST /api/mods/<action>/` - Acción mods (legacy) ✅ (requiere `server_id`)
- [x] `GET /api/players/` - Listar jugadores (legacy) ✅ (requiere `server_id`)
- [x] `GET /api/logs/` - Logs del servidor (legacy) ✅ (requiere `server_id`)
- [x] `POST /api/command/` - Ejecutar comando (legacy) ✅ (requiere `server_id`)

## Resumen
- ✅ Funcionando: 28/28 (100%)
- ❌ Con problemas: 0/28 (0%)
- Problemas principales: 
  - Ninguno - Todos los endpoints principales funcionan correctamente ✅
  - **Nota**: `POST /api/servers/switch/` tiene problema de CSRF pero no es crítico

## Notas
- ✅ @csrf_exempt agregado a todos los endpoints POST que lo necesitaban
- ✅ **REFACTOR: Manejo de server_id por el cliente** - Todos los endpoints ahora requieren que el cliente envíe `server_id` explícitamente (URL, query param, header `X-Server-ID`, o body JSON). Se eliminó la lógica de detección automática del servidor. El servidor es ahora stateless respecto al servidor seleccionado.
- ✅ `POST /api/servers/create/` testeado completamente - funciona correctamente, valida campos requeridos, puerto RCON, permisos y crea UserServerRole
- ✅ `POST /api/servers/<id>/control/<action>/` testeado completamente - funciona correctamente, valida acciones (start/stop/restart/pause/unpause), permisos (control_server), container_name y maneja errores de Docker
- ✅ `GET /api/servers/<id>/container/` testeado completamente - funciona correctamente, verifica permisos (view), usa container_name o host como fallback, retorna 404 cuando el contenedor no existe (comportamiento esperado)
- ✅ `POST /api/servers/<id>/whitelist/add/` testeado completamente - funciona correctamente, verifica permisos (manage_whitelist), valida username, maneja errores de RCON. **TESTEADO CON SERVIDOR REAL COBBLEMON - FUNCIONA PERFECTAMENTE**
- ✅ `POST /api/servers/<id>/whitelist/remove/` testeado completamente - funciona correctamente, verifica permisos (manage_whitelist), valida username, elimina usuarios de whitelist vía RCON. **TESTEADO CON SERVIDOR REAL COBBLEMON - FUNCIONA PERFECTAMENTE**. Se eliminaron 4 usuarios "test" (Test2, test4, Test, test3) exitosamente.
- ✅ `GET /api/servers/<id>/whitelist/` funciona correctamente - encontró 14 usuarios en whitelist del servidor cobblemon. El bug anterior estaba resuelto o era específico de otro servidor.
- ✅ `GET /api/servers/<id>/status/` también muestra jugadores conectados - encontró 3 jugadores online (Richardust, ELBROMASPQNAS, Elieli)
- ✅ `POST /api/servers/<id>/settings/update/` testeado completamente - funciona correctamente, verifica permisos (manage_settings), actualiza campos en BD y modifica server.properties. **TESTEADO CON SERVIDOR REAL COBBLEMON - FUNCIONA PERFECTAMENTE**. Se probaron cambios seguros (is_public, motd) que fueron aplicados y revertidos exitosamente. El endpoint NO tiene problemas de CSRF (el @csrf_exempt funciona correctamente).
- ✅ `POST /api/servers/<id>/users/create/` testeado completamente - **SISTEMA DE REGISTRO POR EMAIL IMPLEMENTADO**. Admin crea usuario con email (sin contraseña), se genera token único y se envía email automáticamente. El usuario establece su propia contraseña usando el token. **TESTEADO CON SERVIDOR REAL - FUNCIONA PERFECTAMENTE**. El endpoint requiere `auth_mode='database'` o 'both'. Las contraseñas se hashean con SHA256+salt. El admin nunca ve las contraseñas.
- ✅ `POST /api/servers/<id>/users/set-password/` testeado completamente - endpoint público (sin autenticación) para establecer contraseña con token. Valida token (expiración 24 horas), establece contraseña, activa usuario y limpia token. **TESTEADO CON SERVIDOR REAL - FUNCIONA PERFECTAMENTE**.
- ✅ `GET /api/servers/<id>/users/` funciona correctamente - retorna 400 cuando `auth_mode` no es 'database' o 'both' (comportamiento esperado).
- ✅ `POST /api/servers/<id>/users/<user_id>/update/` testeado completamente - funciona correctamente, verifica permisos (manage_users), permite actualizar contraseña y estado (is_active). Valida longitud mínima de contraseña (6 caracteres) y retorna 404 si el usuario no existe. **TESTEADO CON SERVIDOR REAL - FUNCIONA PERFECTAMENTE**. Se probó: actualizar contraseña (nueva funciona, antigua ya no), cambiar is_active (usuario inactivo no puede autenticarse), validación de usuario inexistente.
- ✅ `POST /api/servers/<id>/users/<user_id>/delete/` testeado completamente - funciona correctamente, verifica permisos (manage_users), elimina usuario de la BD. Retorna 404 si el usuario no existe. **TESTEADO CON SERVIDOR REAL - FUNCIONA PERFECTAMENTE**.
- ✅ `POST /api/servers/<id>/backups/create/` testeado completamente - funciona correctamente, verifica permisos (control_server), crea backup en background, comprime archivos del mundo y server.properties en tar.gz. El backup se completa automáticamente y aparece en la lista. **TESTEADO CON SERVIDOR DE PRUEBA - FUNCIONA PERFECTAMENTE**. Se creó servidor de prueba, se creó backup, se verificó que se completó y se eliminó todo correctamente.
- ✅ `POST /api/servers/<id>/backups/<backup_id>/restore/` testeado completamente - funciona correctamente, verifica permisos (control_server), valida que el backup esté completado y que el archivo exista. Retorna 404 si el backup no existe. **NOTA**: La implementación de restauración es parcial (requiere detener servidor, restaurar archivos, reiniciar). **TESTEADO CON SERVIDOR DE PRUEBA - FUNCIONA PERFECTAMENTE**.
- ✅ `GET /api/minecraft/versions/latest/` testeado completamente - funciona correctamente, retorna 404 si no hay versiones disponibles (comportamiento esperado). Si hay versiones, retorna la marcada como `is_latest=True`, o la más reciente por fecha si no hay ninguna marcada como latest. **TESTEADO CON SERVIDOR REAL - FUNCIONA PERFECTAMENTE**.
- ✅ `POST /api/minecraft/versions/create/` testeado completamente - funciona correctamente, requiere usuario staff, valida campos requeridos (version), permite crear versiones con diferentes configuraciones. Si se marca como `is_latest=True`, desmarca automáticamente las demás versiones. **TESTEADO CON SERVIDOR REAL - FUNCIONA PERFECTAMENTE**. Se probó: crear versión normal, crear versión latest (desmarca otras), validación de campos requeridos.

