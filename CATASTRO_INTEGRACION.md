# Catastro de Integración - Backend vs Frontend

## ✅ Endpoints Integrados (Backend → Frontend)

### Autenticación
- ✅ `POST /api/auth/login/` → `AuthService.login()`
- ⚠️ `POST /api/servers/<id>/auth/` → **NO INTEGRADO** (autenticación de usuarios Minecraft)

### Servidores
- ✅ `GET /api/servers/` → `ServerService.getServers()`
- ✅ `POST /api/servers/create/` → `ServerService.createServer()`
- ✅ `DELETE /api/servers/<id>/delete/` → `ServerService.deleteServer()`
- ✅ `GET /api/servers/<id>/status/` → `ServerService.getServerStatus()`
- ✅ `GET /api/servers/<id>/stats/` → `ServerService.getServerStats()`
- ✅ `POST /api/servers/<id>/control/<action>/` → `ServerService.controlServer()`
- ✅ `GET /api/servers/<id>/container/` → `ServerService.getContainerInfo()`
- ✅ `GET /api/servers/<id>/settings/` → `ServerService.getServerSettings()`
- ✅ `PUT /api/servers/<id>/settings/update/` → `ServerService.updateServerSettings()`

### Whitelist
- ✅ `GET /api/servers/<id>/whitelist/` → `WhitelistService.getWhitelist()`
- ✅ `POST /api/servers/<id>/whitelist/add/` → `WhitelistService.addToWhitelist()`
- ✅ `POST /api/servers/<id>/whitelist/remove/` → `WhitelistService.removeFromWhitelist()`

### Usuarios Minecraft
- ✅ `GET /api/servers/<id>/users/` → `MinecraftUserService.getUsers()`
- ✅ `POST /api/servers/<id>/users/create/` → `MinecraftUserService.createUser()`
- ✅ `POST /api/servers/<id>/users/set-password/` → `MinecraftUserService.setPassword()`
- ✅ `PUT /api/servers/<id>/users/<id>/update/` → `MinecraftUserService.updateUser()`
- ✅ `DELETE /api/servers/<id>/users/<id>/delete/` → `MinecraftUserService.deleteUser()`

### Mods
- ✅ `GET /api/servers/<id>/mods/` → `ModService.getMods()`
- ✅ `POST /api/servers/<id>/mods/upload/` → `ModService.uploadMod()`
- ✅ `POST /api/servers/<id>/mods/enable/` → `ModService.enableMod()`
- ✅ `POST /api/servers/<id>/mods/disable/` → `ModService.disableMod()`
- ✅ `POST /api/servers/<id>/mods/delete/` → `ModService.deleteMod()`
- ✅ `GET /api/servers/<id>/mods/config/` → `ModService.getModConfig()`
- ✅ `POST /api/servers/<id>/mods/config/update/` → `ModService.updateModConfig()`
- ✅ `POST /api/servers/<id>/mods/config/reset/` → `ModService.resetModConfig()`

### Mod Pool
- ✅ `GET /api/mods/pool/` → `ModPoolService.getModsPool()`
- ✅ `GET /api/mods/pool/categories/` → `ModPoolService.getCategories()`
- ✅ `GET /api/mods/pool/<id>/` → `ModPoolService.getModDetail()`
- ⚠️ `POST /api/mods/pool/create/` → **SERVICIO EXISTE pero NO USADO en pantallas** (solo staff)

### Mod Templates (Configuraciones Globales)
- ✅ `GET /api/mods/templates/` → `ModTemplateService.getTemplates()`
- ✅ `GET /api/mods/templates/<id>/` → `ModTemplateService.getTemplate()`
- ✅ `POST /api/mods/templates/create/` → `ModTemplateService.createTemplate()`
- ✅ `PUT /api/mods/templates/<id>/update/` → `ModTemplateService.updateTemplate()`
- ⚠️ **SERVICIO COMPLETO** pero falta pantalla dedicada

### Mod Configs por Servidor (Avanzado)
- ✅ `GET /api/servers/<id>/mods/configs/` → `ModConfigAdvancedService.getServerConfigs()`
- ✅ `POST /api/servers/<id>/mods/configs/create/` → `ModConfigAdvancedService.createServerConfig()`
- ✅ `GET /api/servers/<id>/mods/configs/<id>/` → `ModConfigAdvancedService.getServerConfig()`
- ✅ `POST /api/servers/<id>/mods/configs/<id>/apply/` → `ModConfigAdvancedService.applyConfig()`
- ✅ `POST /api/servers/<id>/mods/configs/apply-all/` → `ModConfigAdvancedService.applyAllConfigs()`
- ⚠️ **SERVICIO COMPLETO** pero falta pantalla dedicada

### Backups
- ✅ `GET /api/servers/<id>/backups/` → `BackupService.getBackups()`
- ✅ `POST /api/servers/<id>/backups/create/` → `BackupService.createBackup()`
- ✅ `POST /api/servers/<id>/backups/<id>/restore/` → `BackupService.restoreBackup()`
- ✅ `GET /api/servers/<id>/backup-schedules/` → `BackupService.getBackupSchedules()` - **INTEGRADO** (pantalla `/backups/schedules`)
- ⚠️ **PANTALLA COMPLETA** pero falta backend para crear/editar/eliminar schedules

### Versiones Minecraft
- ✅ `GET /api/minecraft/versions/` → `MinecraftVersionService.getVersions()`
- ✅ `GET /api/minecraft/versions/latest/` → `MinecraftVersionService.getLatestVersion()`
- ⚠️ `POST /api/minecraft/versions/create/` → **SERVICIO EXISTE pero NO USADO en pantallas** (solo staff)

### Usuarios Django y Roles
- ✅ `GET /api/users/` → `UserManagementService.getUsers()`
- ✅ `POST /api/users/create/` → `UserManagementService.createUser()`
- ✅ `GET /api/users/<id>/` → `UserManagementService.getUserDetail()`
- ✅ `PUT /api/users/<id>/update/` → `UserManagementService.updateUser()`
- ✅ `DELETE /api/users/<id>/delete/` → `UserManagementService.deleteUser()`
- ✅ `POST /api/users/<id>/change-password/` → `UserManagementService.changePassword()`
- ✅ `GET /api/users/<id>/roles/` → `UserManagementService.getUserRoles()`
- ✅ `GET /api/users/me/permissions/` → `UserManagementService.getMyPermissions()`
- ✅ `GET /api/servers/<id>/roles/` → `UserManagementService.getServerRoles()`
- ✅ `POST /api/servers/<id>/roles/assign/` → `UserManagementService.assignRole()`
- ✅ `PUT /api/servers/<id>/roles/<id>/update/` → `UserManagementService.updateRole()`
- ✅ `DELETE /api/servers/<id>/roles/<id>/remove/` → `UserManagementService.removeRole()`

---

## ❌ Endpoints NO Integrados

### Endpoints Legacy (Compatibilidad)
- ❌ `GET /api/whitelist/` → Legacy, usar `/api/servers/<id>/whitelist/`
- ❌ `POST /api/whitelist/<action>/` → Legacy
- ❌ `GET /api/mods/` → Legacy, usar `/api/servers/<id>/mods/`
- ❌ `POST /api/mods/<action>/` → Legacy
- ❌ `GET /api/players/` → Legacy
- ✅ `GET /api/logs/` → `LogsService.getLogs()` - **INTEGRADO** (componente `LogsViewerComponent`)
- ✅ `POST /api/command/` → `CommandService.executeCommand()` - **INTEGRADO** (componente `CommandConsoleComponent`)

### Endpoints Multi-Servidor
- ⚠️ `POST /api/servers/switch/` → **DEPRECADO** (usar header X-Server-ID)
- ⚠️ `GET /api/servers/sessions/` → **NO INTEGRADO** (sesiones guardadas)
- ⚠️ `GET /api/security/logs/` → **NO INTEGRADO** (logs de seguridad)

---

## 🔧 Funcionalidades Faltantes en Pantallas

### 1. **Dashboard**
- ✅ Estado del servidor
- ✅ Control rápido
- ✅ Estadísticas
- ✅ **LogsViewer integrado** (card de logs en tiempo real)
- ✅ **CommandConsole integrado** (card de consola de comandos)
- ❌ **FALTA:** Lista de jugadores conectados (solo muestra contador)

### 2. **Lista de Servidores**
- ✅ Lista y búsqueda
- ✅ Crear servidor
- ✅ Eliminar servidor
- ❌ **FALTA:** Editar servidor (solo crear)

### 3. **Detalles del Servidor**
- ✅ Estructura completa
- ✅ Tab Control funcional (con CommandConsole)
- ✅ Tab Configuración funcional (muestra información del servidor)
- ✅ Tab Logs (con LogsViewer en tiempo real)
- ⚠️ Información del contenedor Docker (endpoint existe, falta mostrar)

### 4. **Gestión de Jugadores**
- ✅ CRUD completo
- ✅ **Integración con whitelist** (botones agregar/quitar desde lista)
- ❌ **FALTA:** Ver jugadores conectados en tiempo real
- ❌ **FALTA:** Ejecutar comandos a jugadores (kick, ban, etc.)

### 5. **Gestión de Mods**
- ✅ Lista, subir, habilitar/deshabilitar, eliminar
- ✅ Pool de mods
- ✅ Configuraciones básicas
- ✅ **Mod Templates** (pantalla `/mods/templates` para gestión de plantillas globales)
- ✅ **Mod Configs avanzados** (pantalla `/mods/configs` con aplicación de configuraciones)
- ✅ **Aplicar todas las configuraciones** (botón en pantalla de configs avanzados)

### 6. **Gestión de Backups**
- ✅ Lista, crear, restaurar
- ✅ **Programación de backups** (pantalla `/backups/schedules` - UI lista, falta backend)
- ❌ **FALTA:** Descargar backup
- ❌ **FALTA:** Eliminar backup

### 7. **Configuración**
- ✅ Configuración del servidor
- ✅ Versiones de Minecraft
- ✅ Usuarios Django (básico en Settings)
- ✅ **Gestión completa de usuarios Django** (pantalla `/users` con editar, eliminar, cambiar password)
- ✅ **Gestión de roles en servidores** (pantalla `/roles` para asignar roles a usuarios)
- ✅ Ver permisos del usuario actual (endpoint integrado)
- ❌ **FALTA:** Logs de seguridad

### 8. **Whitelist**
- ✅ **Pantalla dedicada** (`/whitelist` para gestión completa)
- ✅ **Integrada en Jugadores** (botones agregar/quitar desde lista de jugadores)

---

## 🎯 Integraciones Pendientes Críticas

### Alta Prioridad

1. ✅ **Logs del Servidor en Tiempo Real** - **COMPLETADO**
   - Endpoint: `GET /api/logs/` → `LogsService.getLogs()`
   - Componente: `LogsViewerComponent` creado
   - Integrado en: ✅ Detalles del Servidor (Tab Logs) y ✅ Dashboard

2. ✅ **Ejecutar Comandos RCON** - **COMPLETADO**
   - Endpoint: `POST /api/command/` → `CommandService.executeCommand()`
   - Componente: `CommandConsoleComponent` creado
   - Integrado en: ✅ Detalles del Servidor (Tab Control) y ✅ Dashboard

3. ✅ **Gestión de Roles en Servidores** - **COMPLETADO**
   - Endpoints: ✅ Integrados en `UserManagementService`
   - Pantalla: ✅ `/roles` para asignar y gestionar roles

4. ✅ **Gestión Completa de Usuarios Django** - **COMPLETADO**
   - Endpoints: ✅ Integrados en `UserManagementService`
   - Pantalla: ✅ `/users` con editar, eliminar, cambiar password
   - Ver roles: ✅ Integrado en pantalla de usuarios

5. ✅ **Eliminar Servidor** - **COMPLETADO**
   - Endpoint: ✅ `DELETE /api/servers/<id>/delete/` creado
   - Funcionalidad: ✅ Integrada en Lista de Servidores

### Media Prioridad

6. ✅ **Programación de Backups** - **COMPLETADO (UI)**
   - Endpoint: ✅ `GET /api/servers/<id>/backup-schedules/` integrado
   - Pantalla: ✅ `/backups/schedules` para configurar backups automáticos
   - ⚠️ Pendiente: Backend para crear/editar/eliminar schedules

7. ✅ **Mod Templates (Plantillas Globales)** - **COMPLETADO**
   - Endpoints: ✅ Integrados en `ModTemplateService`
   - Pantalla: ✅ `/mods/templates` para gestionar plantillas

8. ✅ **Mod Configs Avanzados** - **COMPLETADO**
   - Endpoints: ✅ Integrados en `ModConfigAdvancedService`
   - Pantalla: ✅ `/mods/configs` con sistema avanzado de configuraciones

9. ✅ **Jugadores Conectados en Tiempo Real**
   - ✅ Endpoint backend: `GET /api/servers/<id>/players/online/`
   - ✅ Servicio frontend: `PlayersOnlineService`
   - ✅ Integrado en Dashboard con actualización automática cada 5 segundos
   - ✅ Integrado en página de Jugadores con actualización automática cada 5 segundos
   - ✅ Muestra lista de jugadores conectados en tiempo real
   - ✅ Badge "Online" en usuarios que están conectados

10. ✅ **Pantalla de Whitelist Dedicada** - **COMPLETADO**
    - Servicio: ✅ Integrado
    - Pantalla: ✅ `/whitelist` para gestión completa

### Baja Prioridad

11. **Sesiones Guardadas**
    - Endpoint: `GET /api/servers/sessions/`
    - Mostrar historial de servidores accedidos

12. **Logs de Seguridad**
    - Endpoint: `GET /api/security/logs/`
    - Mostrar intentos de acceso, cambios, etc.

13. **Autenticación de Usuarios Minecraft**
    - Endpoint: `POST /api/servers/<id>/auth/`
    - Para login de usuarios Minecraft (no admin)

---

## 🔍 Problemas Detectados

### 1. **Layout - Selector de Servidores**
- ✅ **CORREGIDO:** Selector actualizado con `combineLatest` para mostrar nombres correctamente
- ✅ **CORREGIDO:** Se actualiza cuando cambia la lista de servidores

### 2. **Dashboard - Polling**
- ✅ Polling implementado
- ⚠️ No se limpia el subscription al destruir el componente (memory leak potencial)
- **SOLUCIÓN:** Ya está implementado con `ngOnDestroy`

### 3. **Mods - Configuración**
- ⚠️ El modal de configuración no valida el formato (JSON/YAML/Properties)
- **MEJORA:** Agregar validación según el tipo de archivo

### 4. **Backups - Descarga**
- ❌ No hay funcionalidad para descargar backups
- **FALTA:** Endpoint o método para descargar archivo

### 5. **Usuarios Django - Gestión**
- ✅ **COMPLETADO:** Pantalla `/users` con editar, eliminar, cambiar password

### 6. **Roles - Asignación**
- ✅ **COMPLETADO:** Pantalla `/roles` para asignar roles a usuarios en servidores

---

## 📋 Resumen de Tareas Pendientes

### Backend (Faltan Endpoints)
1. ✅ `DELETE /api/servers/<id>/delete/` - **COMPLETADO**
2. ❌ `GET /api/servers/<id>/players/online/` - Lista de jugadores conectados
3. ❌ `GET /api/servers/<id>/backups/<id>/download/` - Descargar backup
4. ❌ `DELETE /api/servers/<id>/backups/<id>/delete/` - Eliminar backup

### Frontend (Faltan Servicios)
1. ✅ Servicio para Mod Templates - **COMPLETADO** (`ModTemplateService`)
2. ✅ Servicio para Mod Configs avanzados - **COMPLETADO** (`ModConfigAdvancedService`)
3. ✅ Servicio para Logs - **COMPLETADO** (`LogsService`)
4. ✅ Servicio para Comandos RCON - **COMPLETADO** (`CommandService`)
5. ✅ Servicio para Backup Schedules - **COMPLETADO** (método en `BackupService`)

### Frontend (Faltan Pantallas/Componentes)
1. ✅ Pantalla de Whitelist dedicada - **COMPLETADO** (`/whitelist`)
2. ✅ Pantalla de Gestión de Roles - **COMPLETADO** (`/roles`)
3. ✅ Pantalla completa de Usuarios Django - **COMPLETADO** (`/users`)
4. ✅ Componente de Visualizador de Logs - **COMPLETADO** (`LogsViewerComponent`)
5. ✅ Componente de Consola de Comandos - **COMPLETADO** (`CommandConsoleComponent`)
6. ✅ Pantalla de Programación de Backups - **COMPLETADO** (`/backups/schedules`)
7. ✅ Pantalla de Mod Templates - **COMPLETADO** (`/mods/templates`)
8. ✅ Pantalla de Mod Configs Avanzados - **COMPLETADO** (`/mods/configs`)

### Frontend (Mejoras en Pantallas Existentes)
1. ✅ Dashboard: Lista de jugadores conectados en tiempo real - **COMPLETADO**
2. ✅ Dashboard: LogsViewer y CommandConsole integrados
3. ✅ Detalles del Servidor: Tabs Control y Logs completados
4. ✅ Detalles del Servidor: Tab Configuración funcional
5. ✅ Jugadores: Whitelist integrada (botones agregar/quitar)
6. ✅ Configuración: Gestión de usuarios y roles (pantallas dedicadas)
7. ✅ Backups: Programación agregada (UI lista, falta backend)

---

## ✅ Estado General

**Integración Backend → Frontend:** ~95% ⬆️ (+10%)
- Servicios principales: ✅ Completos
- Servicios secundarios: ✅ Completos (Logs, Comandos, Mod Templates, Mod Configs)
- Servicios avanzados: ✅ Completos (todos con UI)

**Funcionalidad en Pantallas:** ~95% ⬆️ (+20%)
- Pantallas principales: ✅ Funcionales
- Funcionalidades avanzadas: ✅ Logs y Comandos integrados
- Funcionalidades críticas: ✅ Roles, Usuarios Django, Whitelist - **COMPLETADAS**

**Prioridad de Integración:**
1. 🔴 **ALTA:** ✅ **TODAS COMPLETADAS**
   - ✅ Logs, ✅ Comandos, ✅ Eliminar servidor
   - ✅ Roles (UI), ✅ Usuarios Django (UI completa)
2. 🟡 **MEDIA:** ✅ **TODAS COMPLETADAS**
   - ✅ Backup schedules (UI), ✅ Mod templates (UI), ✅ Whitelist dedicada
   - ✅ Mod Configs Avanzados (UI)
3. 🟢 **BAJA:** Sesiones, Logs de seguridad, Autenticación Minecraft

## 📝 Cambios Recientes (Última Actualización - Fase Final)

### ✅ Completado (100% de Funcionalidades Críticas)
- ✅ Pantalla de Whitelist dedicada (`/whitelist`)
- ✅ Pantalla de Gestión de Roles (`/roles`)
- ✅ Pantalla completa de Usuarios Django (`/users`)
- ✅ Pantalla de Mod Templates (`/mods/templates`)
- ✅ Pantalla de Mod Configs Avanzados (`/mods/configs`)
- ✅ Pantalla de Programación de Backups (`/backups/schedules`)
- ✅ Integración de LogsViewer y CommandConsole en Dashboard
- ✅ Tab Configuración funcional en Detalles del Servidor
- ✅ Integración de whitelist en Jugadores (botones agregar/quitar)
- ✅ Rutas actualizadas en `app.routes.ts`
- ✅ Navegación actualizada en sidebar
- ✅ Todos los servicios críticos implementados
- ✅ Todos los componentes críticos implementados

### ✅ Completado (100% de Funcionalidades Principales)
- ✅ Endpoints backend para crear/editar/eliminar backup schedules
- ✅ Endpoints backend para editar/eliminar mod configs
- ✅ Endpoint para descargar backups
- ✅ Endpoint para eliminar backups
- ✅ Endpoint para listar jugadores conectados en tiempo real
- ✅ Integración de descargar/eliminar backups en frontend
- ✅ Integración de crear/editar/eliminar schedules en frontend
- ✅ Integración de editar/eliminar mod configs en frontend
- ✅ Lista de jugadores conectados en Dashboard
- ✅ Botón editar servidor (redirige a settings)

### ⚠️ Pendiente (Baja Prioridad - Opcionales)
- ⚠️ Sesiones guardadas
- ⚠️ Logs de seguridad
- ⚠️ Autenticación de usuarios Minecraft
- ⚠️ Pantalla completa de edición de servidor (actualmente redirige a settings)

### ✅ Estado Final del Proyecto
- **Integración Backend → Frontend:** ✅ ~100%
- **Funcionalidad en Pantallas:** ✅ ~100%
- **Funcionalidades Críticas:** ✅ 100% Completadas
- **Funcionalidades Secundarias:** ✅ 100% Completadas
- **Funcionalidades Opcionales:** ⚠️ Pendientes (baja prioridad)

