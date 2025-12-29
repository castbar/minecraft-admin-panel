# Plugins y Mods Preinstalados

Este documento lista los plugins y mods que vienen preinstalados en la imagen Docker, pero que deben habilitarse manualmente según las necesidades del servidor.

## 🔐 Autenticación y Seguridad

### SimpleAuth (Fabric)
- **Descripción**: Plugin de autenticación ligero para servidores Fabric
- **Uso**: Permite login con contraseñas para servidores en modo offline
- **Habilitación**: 
  - Configurar en `server.properties`: `online-mode=false`
  - El plugin se activa automáticamente
- **Ubicación**: `/data/plugins/simpleauth/` (si Bukkit) o `/data/mods/simpleauth.jar` (si Fabric)

### LoginSecurity (Bukkit/Spigot)
- **Descripción**: Plugin moderno de autenticación con soporte para 2FA
- **Uso**: Alternativa más avanzada para servidores Bukkit/Spigot
- **Habilitación**: 
  - Copiar a `/data/plugins/`
  - Reiniciar servidor
  - Configurar en `/data/plugins/LoginSecurity/config.yml`

## 🛠️ Utilidades Esenciales

### Fabric API
- **Estado**: Siempre activo (requerido)
- **Ubicación**: `/data/mods/fabric-api.jar`

### Cobblemon
- **Estado**: Preinstalado pero opcional
- **Habilitación**: Ya está en `/data/mods/` - se carga automáticamente si está presente

### WorldEdit (Bukkit/Spigot)
- **Descripción**: Herramienta de edición de mundo
- **Ubicación**: `/data/plugins/WorldEdit/`
- **Habilitación**: Se activa automáticamente al reiniciar

### LuckPerms
- **Descripción**: Sistema de permisos moderno
- **Ubicación**: `/data/plugins/LuckPerms/`
- **Habilitación**: Se activa automáticamente al reiniciar

## 📊 Monitoreo

### Spark
- **Descripción**: Profiling y análisis de rendimiento
- **Ubicación**: `/data/plugins/spark.jar` o `/data/mods/spark.jar`
- **Habilitación**: Se activa automáticamente

### ServerStats
- **Descripción**: Estadísticas del servidor
- **Ubicación**: `/data/plugins/ServerStats/`
- **Habilitación**: Se activa automáticamente

## 💬 Comunicación

### ChatControl
- **Descripción**: Control avanzado de chat
- **Ubicación**: `/data/plugins/ChatControl/`
- **Habilitación**: Se activa automáticamente

### DiscordSRV
- **Descripción**: Integración con Discord
- **Ubicación**: `/data/plugins/DiscordSRV/`
- **Habilitación**: Requiere configuración de bot token en `config.yml`

## 📝 Notas

- Todos los plugins/mods están en la imagen pero **NO se cargan automáticamente** si no están en las carpetas correctas
- Para **habilitar** un plugin: copiarlo a la carpeta correspondiente (`/data/plugins/` o `/data/mods/`)
- Para **deshabilitar**: eliminar el archivo o moverlo fuera de la carpeta
- Los plugins se pueden gestionar desde el panel web sin reiniciar el servidor (si soporta hot-reload)

## 🔧 Gestión desde el Panel

Puedes gestionar plugins y mods desde:
- **Panel Web** → **Servidor** → **Mods/Plugins**
- Agregar/eliminar sin reiniciar (si es posible)
- Ver estado de cada plugin/mod

