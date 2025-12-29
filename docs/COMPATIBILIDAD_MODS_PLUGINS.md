# Compatibilidad: Mods vs Plugins

## Diferencia Fundamental

### Mods (Fabric/Forge)
- **Modifican el código del juego** a nivel de cliente y servidor
- Requieren que **todos los jugadores** tengan el mismo mod instalado
- Se instalan en carpeta `mods/`
- Ejemplos: Cobblemon, JEI, WTHIT, Simple Voice Chat (mod)

### Plugins (Bukkit/Spigot/Paper)
- **Extienden el servidor** sin modificar el código del juego
- Solo se instalan en el **servidor**, los jugadores no necesitan nada
- Se instalan en carpeta `plugins/`
- Ejemplos: LuckPerms, WorldEdit, EssentialsX, Simple Voice Chat (plugin)

## Compatibilidad por Tipo de Servidor

| Tipo de Servidor | Mods | Plugins | Notas |
|------------------|------|---------|-------|
| **Vanilla** | ❌ No | ❌ No | Solo servidor oficial, sin modificaciones |
| **Fabric** | ✅ Sí | ❌ No | Solo mods de Fabric |
| **Forge** | ✅ Sí | ❌ No | Solo mods de Forge |
| **Bukkit** | ❌ No | ✅ Sí | Solo plugins |
| **Spigot** | ❌ No | ✅ Sí | Solo plugins (fork de Bukkit) |
| **Paper** | ❌ No | ✅ Sí | Solo plugins (fork de Spigot, mejor rendimiento) |

## Reglas Importantes

1. **No puedes mezclar mods y plugins** en el mismo servidor
2. **Fabric y Forge son incompatibles** - no puedes usar mods de Fabric en Forge y viceversa
3. **Bukkit, Spigot y Paper son compatibles** - los plugins funcionan en los tres
4. **Vanilla no acepta nada** - solo el servidor oficial

## Ejemplos de Mods/Plugins Populares

### Mods (Fabric/Forge)
- **Cobblemon** - Pokémon en Minecraft (Fabric/Forge)
- **JEI/REI** - Ver recetas (Fabric/Forge)
- **WTHIT** - Información de bloques (Fabric)
- **Simple Voice Chat** - Chat de voz (Fabric/Forge)
- **Fabric API** - Requerido para mods de Fabric
- **Forge** - Requerido para mods de Forge

### Plugins (Bukkit/Spigot/Paper)
- **LuckPerms** - Sistema de permisos
- **WorldEdit** - Edición de mundos
- **EssentialsX** - Comandos esenciales
- **Simple Voice Chat** - Chat de voz (plugin)
- **Vault** - API de economía

## Cómo Funciona el Sistema

### 1. Pool de Mods Precargados

El sistema incluye un pool de mods/plugins más usados con:
- Información de compatibilidad
- Configuración por defecto
- Enlaces de descarga
- Categorías

### 2. Listar Mods del Pool

```http
GET /api/mods/pool/?server_type=fabric
```

Filtra automáticamente solo los mods compatibles con Fabric.

### 3. Configurar Mod desde Gestión de Mods

Cuando listas los mods instalados (`GET /api/servers/<id>/mods/`), si el mod está en el pool y tiene configuración, aparece `has_config: true`.

Luego puedes:
- `GET /api/servers/<id>/mods/config/?mod_name=cobblemon.jar` - Ver configuración
- `POST /api/servers/<id>/mods/config/update/` - Editar configuración
- `POST /api/servers/<id>/mods/config/reset/` - Resetear a valores por defecto

## Flujo Recomendado

1. **Crear servidor** con tipo correcto (Fabric, Forge, Paper, etc.)
2. **Listar pool de mods** filtrado por tipo de servidor
3. **Instalar mods/plugins** compatibles
4. **Configurar mods** desde la gestión de mods (botón "Config")

