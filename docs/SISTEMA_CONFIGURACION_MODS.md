# Sistema de Configuración Global de Mods

## Concepto

El sistema permite crear **plantillas globales** de configuración para mods, que luego pueden aplicarse a servidores específicos con personalizaciones opcionales.

## Arquitectura

### 1. Plantillas Globales (`ModConfigTemplate`)

Las plantillas son configuraciones por defecto que se crean una vez y pueden reutilizarse en múltiples servidores.

**Características:**
- **Globales**: Una plantilla puede usarse en todos los servidores
- **Formato flexible**: Soporta JSON, YAML, Properties, TOML, texto plano
- **Ruta configurable**: Define dónde se guarda el archivo de configuración del mod
- **Valores por defecto**: Contiene la configuración base del mod

**Ejemplo de plantilla:**
```json
{
  "mod_name": "cobblemon",
  "display_name": "Cobblemon",
  "config_format": "json",
  "config_file_path": "config/cobblemon.json",
  "default_config": "{\"spawnRate\": 0.5, \"enableShiny\": true}",
  "description": "Configuración de Cobblemon"
}
```

### 2. Configuraciones por Servidor (`ServerModConfig`)

Cada servidor puede tener configuraciones personalizadas basadas en las plantillas.

**Características:**
- **Específicas por servidor**: Cada servidor puede tener su propia configuración
- **Personalizables**: Puede sobrescribir la plantilla o usar la por defecto
- **Habilitación**: Puede habilitarse/deshabilitarse sin eliminar
- **Aplicación**: Escribe el archivo de configuración en el servidor

## Flujo de Uso

### Paso 1: Crear Plantilla Global (Staff)

```http
POST /api/mods/templates/create/
Content-Type: application/json
X-Server-ID: (no requerido, es global)

{
  "mod_name": "cobblemon",
  "display_name": "Cobblemon",
  "config_format": "json",
  "config_file_path": "config/cobblemon.json",
  "default_config": "{\"spawnRate\": 0.5, \"enableShiny\": true}",
  "description": "Configuración de Cobblemon"
}
```

### Paso 2: Aplicar a un Servidor

```http
POST /api/servers/<id>/mods/configs/create/
Content-Type: application/json
X-Server-ID: <server_id>

{
  "template_id": 1,
  "config_content": "{\"spawnRate\": 0.8, \"enableShiny\": true}",  // Opcional, personalizado
  "is_enabled": true
}
```

### Paso 3: Aplicar Configuración al Archivo

```http
POST /api/servers/<id>/mods/configs/<config_id>/apply/
X-Server-ID: <server_id>
```

Esto escribe el archivo de configuración en:
`{minecraft_data_path}/{config_file_path}`

## Formatos Soportados

### JSON
```json
{
  "spawnRate": 0.5,
  "enableShiny": true
}
```

### YAML
```yaml
spawnRate: 0.5
enableShiny: true
```

### Properties
```properties
spawnRate=0.5
enableShiny=true
```

### TOML
```toml
spawnRate = 0.5
enableShiny = true
```

### Texto Plano
Cualquier formato personalizado que el mod use.

## Ejemplos de Uso

### Ejemplo 1: Cobblemon (JSON)

**Plantilla:**
```json
{
  "mod_name": "cobblemon",
  "display_name": "Cobblemon",
  "config_format": "json",
  "config_file_path": "config/cobblemon.json",
  "default_config": "{\"spawnRate\": 0.5, \"enableShiny\": true, \"maxPokemonPerChunk\": 5}"
}
```

**Aplicar a servidor:**
```json
{
  "template_id": 1,
  "config_content": "{\"spawnRate\": 0.8, \"enableShiny\": true, \"maxPokemonPerChunk\": 10}",
  "is_enabled": true
}
```

**Resultado:** Se crea `/data/config/cobblemon.json` con la configuración personalizada.

### Ejemplo 2: JEI (TOML)

**Plantilla:**
```json
{
  "mod_name": "jei",
  "display_name": "JEI",
  "config_format": "toml",
  "config_file_path": "config/jei/jei-client.toml",
  "default_config": "[general]\nsearchMode = \"normal\"\nmaxSearchResults = 100"
}
```

### Ejemplo 3: WTHIT (Properties)

**Plantilla:**
```json
{
  "mod_name": "wthit",
  "display_name": "WTHIT",
  "config_format": "properties",
  "config_file_path": "config/wthit.properties",
  "default_config": "showEntityInfo=true\nshowBlockInfo=true"
}
```

## Ventajas

1. **Centralización**: Una sola plantilla para todos los servidores
2. **Personalización**: Cada servidor puede tener su propia configuración
3. **Flexibilidad**: Soporta múltiples formatos de archivo
4. **Reutilización**: Una plantilla puede usarse en múltiples servidores
5. **Mantenimiento**: Actualizar la plantilla afecta a todos los servidores que la usan (si no tienen personalización)

## Endpoints

### Plantillas Globales (Staff)
- `GET /api/mods/templates/` - Listar plantillas
- `GET /api/mods/templates/<id>/` - Detalles de plantilla
- `POST /api/mods/templates/create/` - Crear plantilla
- `POST /api/mods/templates/<id>/update/` - Actualizar plantilla

### Configuraciones por Servidor
- `GET /api/servers/<id>/mods/configs/` - Listar configuraciones del servidor
- `GET /api/servers/<id>/mods/configs/<config_id>/` - Detalles de configuración
- `POST /api/servers/<id>/mods/configs/create/` - Crear/actualizar configuración
- `POST /api/servers/<id>/mods/configs/<config_id>/apply/` - Aplicar configuración
- `POST /api/servers/<id>/mods/configs/apply-all/` - Aplicar todas las configuraciones

## Notas Importantes

1. **Validación JSON**: Si el formato es JSON, se valida automáticamente
2. **Rutas relativas**: `config_file_path` es relativo a `minecraft_data_path`
3. **Aplicación manual**: Las configuraciones NO se aplican automáticamente, debe llamarse `apply`
4. **Habilitación**: Solo las configuraciones con `is_enabled=true` se pueden aplicar
5. **Personalización**: Si `config_content` está vacío, se usa la plantilla por defecto

