# Ejemplo: Configurar Chat de Proximidad

## Mods de Chat de Proximidad Comunes

Los mods más populares son:
- **Simple Voice Chat** (Fabric/Forge) - Usa JSON
- **Plasmo Voice** (Fabric/Forge) - Usa JSON
- **Proximity Voice Chat** - Usa JSON/YAML

## Ejemplo: Simple Voice Chat

### Paso 1: Crear Plantilla Global (Staff)

El mod Simple Voice Chat guarda su configuración en `config/simple-voice-chat.json`.

**Crear plantilla:**

```http
POST /api/mods/templates/create/
Content-Type: application/json
Authorization: Bearer <token>

{
  "mod_name": "simple-voice-chat",
  "display_name": "Simple Voice Chat",
  "config_format": "json",
  "config_file_path": "config/simple-voice-chat.json",
  "default_config": "{\n  \"voiceChat\": {\n    \"maxPriorityDistance\": 48.0,\n    \"minPriorityDistance\": 8.0,\n    \"fadeDistance\": 16.0,\n    \"enableVoiceActivation\": true,\n    \"voiceActivationThreshold\": -50.0,\n    \"enableSpatialAudio\": true,\n    \"enableWhisperDistance\": true,\n    \"whisperDistance\": 4.0,\n    \"shoutDistance\": 96.0,\n    \"enableCaveCulling\": true,\n    \"caveCullingDistance\": 32.0,\n    \"enableMuffling\": true,\n    \"mufflingBlockPercentage\": 0.5\n  },\n  \"server\": {\n    \"port\": 24477,\n    \"bindAddress\": \"0.0.0.0\",\n    \"enableUdp\": true,\n    \"enableTcp\": true,\n    \"enableIpWhitelist\": false,\n    \"enableIpWhitelistForOp\": false\n  },\n  \"advanced\": {\n    \"compression\": \"OPUS\",\n    \"voiceHostDistance\": 48.0,\n    \"enablePlayerList\": true,\n    \"enablePlayerIcons\": true\n  }\n}",
  "description": "Configuración por defecto de Simple Voice Chat con distancias estándar y audio espacial habilitado"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Template Simple Voice Chat created",
  "data": {
    "id": 1,
    "mod_name": "simple-voice-chat",
    "display_name": "Simple Voice Chat"
  }
}
```

### Paso 2: Aplicar a Servidor con Configuración Personalizada

**Ejemplo: Servidor "Cobblemon" - Chat más cercano (más inmersivo):**

```http
POST /api/servers/1/mods/configs/create/
Content-Type: application/json
X-Server-ID: 1

{
  "template_id": 1,
  "config_content": "{\n  \"voiceChat\": {\n    \"maxPriorityDistance\": 32.0,\n    \"minPriorityDistance\": 4.0,\n    \"fadeDistance\": 12.0,\n    \"enableVoiceActivation\": true,\n    \"voiceActivationThreshold\": -50.0,\n    \"enableSpatialAudio\": true,\n    \"enableWhisperDistance\": true,\n    \"whisperDistance\": 2.0,\n    \"shoutDistance\": 64.0,\n    \"enableCaveCulling\": true,\n    \"caveCullingDistance\": 24.0,\n    \"enableMuffling\": true,\n    \"mufflingBlockPercentage\": 0.6\n  },\n  \"server\": {\n    \"port\": 24477,\n    \"bindAddress\": \"0.0.0.0\",\n    \"enableUdp\": true,\n    \"enableTcp\": true,\n    \"enableIpWhitelist\": false,\n    \"enableIpWhitelistForOp\": false\n  },\n  \"advanced\": {\n    \"compression\": \"OPUS\",\n    \"voiceHostDistance\": 32.0,\n    \"enablePlayerList\": true,\n    \"enablePlayerIcons\": true\n  }\n}",
  "is_enabled": true
}
```

**Ejemplo: Servidor "Survival" - Chat más amplio (más social):**

```http
POST /api/servers/2/mods/configs/create/
Content-Type: application/json
X-Server-ID: 2

{
  "template_id": 1,
  "config_content": "{\n  \"voiceChat\": {\n    \"maxPriorityDistance\": 64.0,\n    \"minPriorityDistance\": 12.0,\n    \"fadeDistance\": 24.0,\n    \"enableVoiceActivation\": true,\n    \"voiceActivationThreshold\": -50.0,\n    \"enableSpatialAudio\": true,\n    \"enableWhisperDistance\": true,\n    \"whisperDistance\": 6.0,\n    \"shoutDistance\": 128.0,\n    \"enableCaveCulling\": true,\n    \"caveCullingDistance\": 48.0,\n    \"enableMuffling\": true,\n    \"mufflingBlockPercentage\": 0.4\n  },\n  \"server\": {\n    \"port\": 24477,\n    \"bindAddress\": \"0.0.0.0\",\n    \"enableUdp\": true,\n    \"enableTcp\": true,\n    \"enableIpWhitelist\": false,\n    \"enableIpWhitelistForOp\": false\n  },\n  \"advanced\": {\n    \"compression\": \"OPUS\",\n    \"voiceHostDistance\": 64.0,\n    \"enablePlayerList\": true,\n    \"enablePlayerIcons\": true\n  }\n}",
  "is_enabled": true
}
```

### Paso 3: Aplicar Configuración al Servidor

Una vez creada la configuración, se aplica escribiendo el archivo:

```http
POST /api/servers/1/mods/configs/1/apply/
X-Server-ID: 1
```

Esto crea/actualiza el archivo:
`/data/config/simple-voice-chat.json`

### Paso 4: Aplicar Todas las Configuraciones

Si tienes múltiples mods configurados, puedes aplicar todas de una vez:

```http
POST /api/servers/1/mods/configs/apply-all/
X-Server-ID: 1
```

## Ejemplo: Plasmo Voice

### Plantilla para Plasmo Voice

```http
POST /api/mods/templates/create/
Content-Type: application/json

{
  "mod_name": "plasmo-voice",
  "display_name": "Plasmo Voice",
  "config_format": "json",
  "config_file_path": "config/plasmo-voice-server.json",
  "default_config": "{\n  \"voice\": {\n    \"distance\": 48.0,\n    \"priorityDistance\": 8.0,\n    \"fadeDistance\": 16.0,\n    \"codec\": \"OPUS\",\n    \"stereo\": true,\n    \"enableWhisper\": true,\n    \"whisperDistance\": 4.0,\n    \"shoutDistance\": 96.0\n  },\n  \"server\": {\n    \"port\": 24477,\n    \"bindAddress\": \"0.0.0.0\",\n    \"enableUdp\": true\n  },\n  \"advanced\": {\n    \"enableSpatialAudio\": true,\n    \"enableCaveCulling\": true,\n    \"caveCullingDistance\": 32.0\n  }\n}",
  "description": "Configuración por defecto de Plasmo Voice"
}
```

## Comparación de Configuraciones

### Servidor "Cobblemon" (Chat Cercano)
- **maxPriorityDistance**: 32.0 (más cercano)
- **whisperDistance**: 2.0 (susurros muy cercanos)
- **shoutDistance**: 64.0 (gritos moderados)
- **Uso**: Más inmersivo, comunicación cercana

### Servidor "Survival" (Chat Amplio)
- **maxPriorityDistance**: 64.0 (más amplio)
- **whisperDistance**: 6.0 (susurros más amplios)
- **shoutDistance**: 128.0 (gritos muy amplios)
- **Uso**: Más social, comunicación a distancia

### Servidor "Creative" (Usa Plantilla por Defecto)
- No tiene `config_content` personalizado
- Usa la configuración de la plantilla
- **Uso**: Valores estándar para todos

## Flujo Completo

1. **Staff crea plantilla** → Una vez, reutilizable
2. **Admin aplica a servidor** → Con o sin personalización
3. **Admin aplica configuración** → Escribe archivo en servidor
4. **Servidor reinicia** → Carga nueva configuración (opcional, algunos mods recargan automáticamente)

## Ventajas del Sistema

1. **Una plantilla, múltiples servidores**: Creas la plantilla una vez, la usas en todos
2. **Personalización fácil**: Cada servidor puede tener su propia configuración
3. **Mantenimiento simple**: Actualizas la plantilla, afecta a todos (si no tienen personalización)
4. **Formato flexible**: Funciona con JSON, YAML, Properties, TOML, etc.

## Notas Importantes

- **Reinicio del servidor**: Algunos mods requieren reiniciar el servidor para aplicar cambios
- **Validación**: El sistema valida JSON automáticamente
- **Rutas**: `config_file_path` es relativo a `minecraft_data_path` del servidor
- **Aplicación manual**: Las configuraciones NO se aplican automáticamente, debes llamar `apply`

