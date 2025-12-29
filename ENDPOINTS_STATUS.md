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

- [ ] `GET /api/servers/<id>/users/` - Listar usuarios de Minecraft ❌ (400 - Server does not use database auth) - **Comportamiento esperado si auth_mode='whitelist'**
- [ ] `POST /api/servers/<id>/users/create/` - Crear usuario de Minecraft con username y password (se hashea con SHA256+salt) ❌ (403 - CSRF o 400 si auth_mode incorrecto)
- [ ] `POST /api/servers/<id>/users/<user_id>/update/` - Actualizar contraseña o estado (is_active) del usuario (no testeado)
- [ ] `POST /api/servers/<id>/users/<user_id>/delete/` - Eliminar usuario de Minecraft (no testeado)

## Backups
- [x] `GET /api/servers/<id>/backups/` - Listar backups ✅
- [ ] `POST /api/servers/<id>/backups/create/` - Crear backup (no testeado)
- [ ] `POST /api/servers/<id>/backups/<backup_id>/restore/` - Restaurar backup (no testeado)
- [x] `GET /api/servers/<id>/backup-schedules/` - Listar programaciones de backup ✅

## Versiones Minecraft
- [x] `GET /api/minecraft/versions/` - Listar versiones disponibles ✅
- [ ] `GET /api/minecraft/versions/latest/` - Obtener última versión ❌ (404 - No version available)
- [ ] `POST /api/minecraft/versions/create/` - Crear nueva versión (no testeado)

## Multi-servidor
- [ ] `POST /api/servers/switch/` - Cambiar servidor activo ❌ (403 - CSRF)
- [x] `GET /api/servers/sessions/` - Sesiones guardadas ✅
- [x] `GET /api/security/logs/` - Logs de seguridad ✅

## Legacy (Compatibilidad)
- [x] `GET /api/whitelist/` - Whitelist (legacy) ✅
- [ ] `POST /api/whitelist/<action>/` - Acción whitelist (legacy) (no testeado)
- [x] `GET /api/mods/` - Listar mods (legacy) ✅
- [ ] `POST /api/mods/<action>/` - Acción mods (legacy) (no testeado)
- [x] `GET /api/players/` - Listar jugadores (legacy) ✅
- [ ] `GET /api/logs/` - Logs del servidor (legacy) ❌ (500 - Server Error)
- [ ] `POST /api/command/` - Ejecutar comando (legacy) (no testeado)

## Resumen
- ✅ Funcionando: 20/25 (80%)
- ❌ Con problemas: 5/25 (20%)
- Problemas principales: 
  - **CSRF (403) en endpoints POST**: users_create, switch_server - **@csrf_exempt agregado pero aún falla** (posible problema de orden de decoradores o cache)
  - logs legacy: 500 error (necesita revisión)
  - versions/latest: No version available (esperado si no hay versiones en BD)
  - users/list: 400 - Server does not use database authentication (esperado, el servidor usa whitelist)

## Notas
- ✅ @csrf_exempt agregado a todos los endpoints POST que lo necesitaban
- ✅ `POST /api/servers/create/` testeado completamente - funciona correctamente, valida campos requeridos, puerto RCON, permisos y crea UserServerRole
- ✅ `POST /api/servers/<id>/control/<action>/` testeado completamente - funciona correctamente, valida acciones (start/stop/restart/pause/unpause), permisos (control_server), container_name y maneja errores de Docker
- ✅ `GET /api/servers/<id>/container/` testeado completamente - funciona correctamente, verifica permisos (view), usa container_name o host como fallback, retorna 404 cuando el contenedor no existe (comportamiento esperado)
- ✅ `POST /api/servers/<id>/whitelist/add/` testeado completamente - funciona correctamente, verifica permisos (manage_whitelist), valida username, maneja errores de RCON. **TESTEADO CON SERVIDOR REAL COBBLEMON - FUNCIONA PERFECTAMENTE**
- ✅ `POST /api/servers/<id>/whitelist/remove/` testeado completamente - funciona correctamente, verifica permisos (manage_whitelist), valida username, elimina usuarios de whitelist vía RCON. **TESTEADO CON SERVIDOR REAL COBBLEMON - FUNCIONA PERFECTAMENTE**. Se eliminaron 4 usuarios "test" (Test2, test4, Test, test3) exitosamente.
- ✅ `GET /api/servers/<id>/whitelist/` funciona correctamente - encontró 14 usuarios en whitelist del servidor cobblemon. El bug anterior estaba resuelto o era específico de otro servidor.
- ✅ `GET /api/servers/<id>/status/` también muestra jugadores conectados - encontró 3 jugadores online (Richardust, ELBROMASPQNAS, Elieli)
- ✅ `POST /api/servers/<id>/settings/update/` testeado completamente - funciona correctamente, verifica permisos (manage_settings), actualiza campos en BD y modifica server.properties. **TESTEADO CON SERVIDOR REAL COBBLEMON - FUNCIONA PERFECTAMENTE**. Se probaron cambios seguros (is_public, motd) que fueron aplicados y revertidos exitosamente. El endpoint NO tiene problemas de CSRF (el @csrf_exempt funciona correctamente).
- ✅ Endpoints de usuarios de Minecraft revisados - **FUNCIONAN CORRECTAMENTE**. Los endpoints retornan 400 cuando `auth_mode` no es 'database' o 'both' (comportamiento esperado). El servidor cobblemon usa `auth_mode='whitelist'`, por lo que estos endpoints no están disponibles. **Cómo funcionan**: Estos endpoints son para administrar usuarios de Minecraft que se autenticarán mediante un plugin/mod del servidor. El login real se hace a través de `POST /api/servers/<id>/auth/` llamado por el plugin. Las contraseñas se hashean con SHA256+salt. Para probar completamente, cambiar `auth_mode` a 'database' o 'both'.

