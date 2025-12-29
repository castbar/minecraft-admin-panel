# Estado de Endpoints - Django API

## Autenticación
- [x] `POST /api/auth/login/` - Login de usuario ✅
- [ ] `POST /api/servers/<id>/auth/` - Autenticación de usuario Minecraft ❌ (401 - Invalid credentials, esperado)

## Servidores
- [x] `GET /api/servers/` - Listar servidores disponibles ✅
- [ ] `POST /api/servers/create/` - Crear nuevo servidor (no testeado)
- [x] `GET /api/servers/<id>/status/` - Estado del servidor ✅
- [x] `GET /api/servers/<id>/stats/` - Estadísticas del servidor ✅
- [ ] `POST /api/servers/<id>/control/<action>/` - Control del servidor ❌ (403 - CSRF)
- [ ] `GET /api/servers/<id>/container/` - Información del contenedor ❌ (404 - docker not found)

## Whitelist
- [x] `GET /api/servers/<id>/whitelist/` - Listar usuarios en whitelist ✅ (pero devuelve 0, bug)
- [ ] `POST /api/servers/<id>/whitelist/add/` - Agregar usuario a whitelist ❌ (403 - CSRF)
- [ ] `POST /api/servers/<id>/whitelist/remove/` - Eliminar usuario de whitelist ❌ (403 - CSRF)

## Configuración
- [x] `GET /api/servers/<id>/settings/` - Obtener configuración del servidor ✅
- [ ] `POST /api/servers/<id>/settings/update/` - Actualizar configuración ❌ (403 - CSRF)

## Usuarios Minecraft
- [ ] `GET /api/servers/<id>/users/` - Listar usuarios de Minecraft ❌ (400 - Server does not use database auth)
- [ ] `POST /api/servers/<id>/users/create/` - Crear usuario de Minecraft ❌ (403 - CSRF)
- [ ] `POST /api/servers/<id>/users/<user_id>/update/` - Actualizar usuario (no testeado)
- [ ] `POST /api/servers/<id>/users/<user_id>/delete/` - Eliminar usuario (no testeado)

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
- ✅ Funcionando: 14/25 (56%)
- ❌ Con problemas: 11/25 (44%)
- Problemas principales: 
  - **CSRF (403) en endpoints POST**: whitelist_add/remove, server_control, settings_update, users_create, switch_server - **@csrf_exempt agregado pero aún falla** (posible problema de orden de decoradores o cache)
  - **whitelist_list**: devuelve 0 jugadores aunque RCON funciona correctamente (14 jugadores detectados) - **BUG CRÍTICO**
  - container_info: docker not found (esperado si docker no está en PATH del contenedor)
  - logs legacy: 500 error (necesita revisión)
  - versions/latest: No version available (esperado si no hay versiones en BD)
  - users/list: 400 - Server does not use database authentication (esperado, el servidor usa whitelist)

## Notas
- ✅ @csrf_exempt agregado a todos los endpoints POST que lo necesitaban
- ⚠️ whitelist_list tiene bug: el parsing funciona en pruebas directas pero el endpoint devuelve vacío (necesita debug)
- ⚠️ Rebuild completo realizado - verificar si los cambios se aplicaron correctamente

