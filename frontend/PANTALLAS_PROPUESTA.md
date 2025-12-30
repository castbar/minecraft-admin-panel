# Propuesta de Pantallas - Minecraft Admin Panel

## 📱 Estructura de Navegación

### 1. **Dashboard** (`/dashboard`)
**Propósito:** Vista principal con resumen del servidor activo

**Componentes:**
- **Card de Estado del Servidor**
  - Estado (Running/Stopped)
  - Conexión RCON (Connected/Disconnected)
  - Uptime
  - Uso de CPU y Memoria
  - Botones de control rápido (Start/Stop/Restart)

- **Card de Jugadores**
  - Jugadores online / Máximo
  - Lista de jugadores conectados (con avatares si es posible)
  - Botón rápido para ver todos los jugadores

- **Card de Estadísticas Rápidas**
  - Total de mods instalados
  - Último backup
  - Espacio en disco usado

- **Card de Acciones Rápidas**
  - Crear backup
  - Ver logs
  - Gestionar whitelist
  - Configuración rápida

**Servicios utilizados:**
- `ServerService.getServerStatus()`
- `ServerService.getServerStats()`
- `ServerService.controlServer()`

---

### 2. **Lista de Servidores** (`/servers`)
**Propósito:** Ver y gestionar todos los servidores disponibles

**Componentes:**
- **Lista de Servidores**
  - Card por servidor con:
    - Nombre del servidor
    - Tipo (Vanilla/Fabric/Forge/etc.)
    - Estado (Running/Stopped)
    - Versión de Minecraft
    - Jugadores online
    - Acciones: Ver detalles, Control, Configuración

- **FAB (Floating Action Button)**
  - Botón para crear nuevo servidor

- **Filtros/Búsqueda**
  - Buscar por nombre
  - Filtrar por tipo
  - Filtrar por estado

**Servicios utilizados:**
- `ServerService.getServers()`
- `ServerService.createServer()`

**Pantallas relacionadas:**
- Modal/Page: Crear Servidor
- Modal/Page: Detalles del Servidor

---

### 3. **Detalles del Servidor** (`/servers/:id`)
**Propósito:** Vista detallada de un servidor específico

**Componentes:**
- **Header con Tabs:**
  - Overview (por defecto)
  - Control
  - Configuración
  - Logs

- **Tab Overview:**
  - Información completa del servidor
  - Estadísticas en tiempo real (con polling)
  - Gráficos de uso de recursos (CPU, Memoria)
  - Historial de acciones recientes

- **Tab Control:**
  - Botones de control (Start/Stop/Restart/Pause/Unpause)
  - Estado del contenedor Docker
  - Información del contenedor

- **Tab Configuración:**
  - Formulario de configuración del servidor
  - Campos editables (max_players, difficulty, pvp_enabled, etc.)
  - Guardar cambios

- **Tab Logs:**
  - Visualizador de logs en tiempo real
  - Filtros de búsqueda
  - Descargar logs

**Servicios utilizados:**
- `ServerService.getServerStatus()`
- `ServerService.getServerStats()`
- `ServerService.getContainerInfo()`
- `ServerService.controlServer()`
- `ServerService.updateServerSettings()`

---

### 4. **Gestión de Jugadores** (`/players`)
**Propósito:** Gestionar jugadores del servidor activo

**Componentes:**
- **Lista de Jugadores**
  - Tabla/Lista con:
    - Username
    - UUID (si disponible)
    - Estado (Online/Offline)
    - Última conexión
    - Acciones: Ver detalles, Editar, Eliminar

- **Filtros:**
  - Buscar por nombre
  - Filtrar por estado (Online/Offline)
  - Filtrar por operadores

- **FAB:**
  - Crear nuevo usuario de Minecraft

- **Acciones:**
  - Agregar a whitelist (si no está)
  - Remover de whitelist
  - Hacer operador
  - Quitar operador

**Servicios utilizados:**
- `MinecraftUserService.getUsers()`
- `MinecraftUserService.createUser()`
- `MinecraftUserService.updateUser()`
- `MinecraftUserService.deleteUser()`
- `WhitelistService.addToWhitelist()`
- `WhitelistService.removeFromWhitelist()`

**Pantallas relacionadas:**
- Modal: Crear Usuario
- Modal: Editar Usuario
- Modal: Confirmar eliminación

---

### 5. **Gestión de Mods** (`/mods`)
**Propósito:** Gestionar mods/plugins del servidor

**Componentes:**
- **Tabs:**
  - Mods Instalados
  - Pool de Mods
  - Configuraciones

- **Tab Mods Instalados:**
  - Lista de mods con:
    - Nombre
    - Estado (Enabled/Disabled)
    - Tamaño del archivo
    - Versión (si disponible)
    - Acciones: Habilitar/Deshabilitar, Configurar, Eliminar
  - FAB: Subir nuevo mod
  - Filtros: Buscar, Filtrar por estado

- **Tab Pool de Mods:**
  - Grid/Lista de mods disponibles del pool
  - Filtros:
    - Por categoría
    - Por tipo de servidor compatible
    - Buscar por nombre
  - Card de mod con:
    - Nombre
    - Descripción
    - Categoría
    - Compatibilidad
    - Botón: Instalar/Descargar

- **Tab Configuraciones:**
  - Lista de mods con configuración disponible
  - Editor de configuración (JSON/YAML/Properties según el tipo)
  - Botón: Resetear a default
  - Botón: Aplicar cambios

**Servicios utilizados:**
- `ModService.getMods()`
- `ModService.uploadMod()`
- `ModService.enableMod()`
- `ModService.disableMod()`
- `ModService.deleteMod()`
- `ModService.getModConfig()`
- `ModService.updateModConfig()`
- `ModService.resetModConfig()`
- `ModPoolService.getModsPool()`
- `ModPoolService.getCategories()`

**Pantallas relacionadas:**
- Modal: Subir Mod
- Modal: Configurar Mod
- Modal: Detalles del Mod (del pool)

---

### 6. **Gestión de Backups** (`/backups`)
**Propósito:** Gestionar backups del servidor

**Componentes:**
- **Lista de Backups**
  - Card por backup con:
    - Fecha y hora
    - Tamaño del archivo
    - Descripción (si tiene)
    - Acciones: Descargar, Restaurar, Eliminar

- **FAB:**
  - Crear backup manual

- **Sección de Programación:**
  - Lista de backups programados
  - Configurar backup automático
  - Habilitar/Deshabilitar programación

- **Filtros:**
  - Buscar por fecha
  - Ordenar por fecha/tamaño

**Servicios utilizados:**
- `BackupService.getBackups()`
- `BackupService.createBackup()`
- `BackupService.restoreBackup()`
- `BackupService.getBackupSchedules()`

**Pantallas relacionadas:**
- Modal: Crear Backup
- Modal: Confirmar Restauración
- Modal: Configurar Backup Automático

---

### 7. **Configuración** (`/settings`)
**Propósito:** Configuración general y del servidor

**Componentes:**
- **Tabs:**
  - Servidor
  - Versiones de Minecraft
  - Seguridad
  - Sistema

- **Tab Servidor:**
  - Formulario completo de configuración del servidor
  - Todos los campos editables
  - Validaciones
  - Guardar cambios

- **Tab Versiones de Minecraft:**
  - Lista de versiones disponibles
  - FAB: Agregar nueva versión
  - Indicador de versión más reciente
  - Filtrar por tipo (release/snapshot)

- **Tab Seguridad:**
  - Logs de seguridad
  - Sesiones activas
  - Historial de accesos

- **Tab Sistema:**
  - Información del sistema
  - Espacio en disco
  - Versión de la aplicación

**Servicios utilizados:**
- `ServerService.getServerSettings()`
- `ServerService.updateServerSettings()`
- `MinecraftVersionService.getVersions()`
- `MinecraftVersionService.getLatestVersion()`
- `MinecraftVersionService.createVersion()`

**Pantallas relacionadas:**
- Modal: Agregar Versión de Minecraft

---

## 🔄 Flujos Importantes

### Flujo de Selección de Servidor
1. Usuario selecciona servidor desde el selector en el header
2. `AuthService.setCurrentServerId()` actualiza el estado
3. `ServerIdInterceptor` agrega automáticamente el header `X-Server-ID`
4. Todas las peticiones siguientes usan ese servidor

### Flujo de Autenticación
1. Usuario ingresa credenciales en `/auth/login`
2. `AuthService.login()` hace la petición
3. Si es exitoso, guarda el estado y redirige a `/dashboard`
4. `AuthGuard` protege las rutas que requieren autenticación

### Flujo de Creación de Usuario Minecraft
1. Admin crea usuario desde `/players`
2. Se envía email al usuario (si tiene email)
3. Usuario recibe token y puede establecer su contraseña
4. Usuario puede iniciar sesión en el servidor

---

## 📦 Componentes Reutilizables Necesarios

1. **ServerCard** - Card para mostrar información de servidor
2. **PlayerCard** - Card para mostrar información de jugador
3. **ModCard** - Card para mostrar información de mod
4. **BackupCard** - Card para mostrar información de backup
5. **StatusBadge** - Badge para mostrar estados (Running/Stopped)
6. **ConfirmModal** - Modal de confirmación genérico
7. **LoadingSpinner** - Spinner de carga
8. **EmptyState** - Estado vacío cuando no hay datos
9. **SearchBar** - Barra de búsqueda reutilizable
10. **FilterChips** - Chips para filtros

---

## 🎨 Consideraciones de UX

1. **Feedback Visual:**
   - Toasts para acciones exitosas/fallidas
   - Loading states en botones
   - Skeleton loaders mientras carga

2. **Navegación:**
   - Breadcrumbs en vistas detalladas
   - Botón "Volver" donde sea necesario
   - Menú lateral siempre accesible

3. **Responsive:**
   - Diseño adaptativo para móvil/tablet/desktop
   - Menú lateral colapsable en móvil

4. **Accesibilidad:**
   - Labels descriptivos
   - Contraste adecuado
   - Navegación por teclado

---

## 🚀 Orden de Implementación Sugerido

1. **Fase 1 - Base:**
   - Dashboard básico
   - Lista de servidores
   - Detalles del servidor (Overview y Control)

2. **Fase 2 - Gestión:**
   - Gestión de jugadores
   - Gestión de whitelist
   - Configuración del servidor

3. **Fase 3 - Mods:**
   - Lista de mods instalados
   - Subir/habilitar/deshabilitar mods
   - Pool de mods

4. **Fase 4 - Avanzado:**
   - Configuración de mods
   - Backups
   - Versiones de Minecraft
   - Logs en tiempo real

