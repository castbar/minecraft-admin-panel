# Propuesta: Manejo de Server ID por el Cliente

## Problema Actual

El sistema actual intenta "detectar" o "recordar" qué servidor está activo del lado del servidor usando:
- `ServerSession` (sesiones guardadas)
- `switch_server` endpoint
- Detección automática por hostname/IP

Esto es problemático porque:
- El servidor no debería "recordar" estado del cliente
- El cliente debe tener control total sobre qué servidor está usando
- Es más simple y RESTful que el cliente envíe siempre el `server_id`

## Solución Propuesta

### 1. El cliente SIEMPRE envía `server_id`

**Opciones (en orden de preferencia):**

#### Opción A: En la URL (RECOMENDADO - ya implementado en endpoints nuevos)
```
GET /api/servers/<server_id>/status/
POST /api/servers/<server_id>/control/start/
GET /api/servers/<server_id>/whitelist/
```

#### Opción B: Header HTTP (alternativa para endpoints legacy)
```
X-Server-ID: <server_id>
```

#### Opción C: Query Parameter (fallback)
```
?server_id=<server_id>
```

### 2. Eliminar o simplificar `switch_server`

**Opción 1: Eliminar completamente**
- El cliente maneja qué servidor está seleccionado
- No necesita notificar al servidor

**Opción 2: Simplificar (solo para guardar sesión opcional)**
- Si el cliente quiere guardar una sesión (para mostrar "último servidor usado"), puede llamar a este endpoint
- Pero NO es necesario para usar otros endpoints

### 3. Migrar endpoints legacy

Los endpoints legacy que no tienen `server_id` en la URL deberían:
- Aceptar `server_id` como query parameter: `?server_id=<id>`
- O aceptar header: `X-Server-ID: <id>`
- O migrar a la nueva estructura: `/api/servers/<id>/...`

**Endpoints legacy a migrar:**
- `GET /api/whitelist/` → `GET /api/servers/<id>/whitelist/` ✅ (ya existe)
- `POST /api/whitelist/<action>/` → `POST /api/servers/<id>/whitelist/<action>/` ✅ (ya existe)
- `GET /api/mods/` → `GET /api/servers/<id>/mods/` (crear nuevo)
- `POST /api/mods/<action>/` → `POST /api/servers/<id>/mods/<action>/` (crear nuevo)
- `GET /api/players/` → `GET /api/servers/<id>/players/` (crear nuevo)
- `GET /api/logs/` → `GET /api/servers/<id>/logs/` (crear nuevo)
- `POST /api/command/` → `POST /api/servers/<id>/command/` (crear nuevo)

### 4. Eliminar lógica de detección automática

Eliminar o simplificar:
- `_detect_server_from_request()` - solo para casos especiales (dashboard)
- `_get_user_server()` - simplificar, requerir `server_id` siempre
- `ServerSession` - mantener solo para historial/último usado (opcional)

## Implementación Sugerida

### Middleware o Helper Function

Crear una función helper que obtenga `server_id` de múltiples fuentes:

```python
def get_server_id_from_request(request):
    """
    Obtener server_id de la request en este orden:
    1. URL parameter (path): /api/servers/<id>/...
    2. Query parameter: ?server_id=<id>
    3. Header: X-Server-ID
    """
    # 1. De la URL (si está en el path)
    if hasattr(request, 'server_id'):
        return request.server_id
    
    # 2. Query parameter
    server_id = request.GET.get('server_id')
    if server_id:
        return int(server_id)
    
    # 3. Header
    server_id = request.headers.get('X-Server-ID')
    if server_id:
        return int(server_id)
    
    return None
```

### Endpoints que NO necesitan server_id

Algunos endpoints son globales y no necesitan `server_id`:
- `GET /api/servers/` - Lista todos los servidores
- `GET /api/servers/sessions/` - Sesiones del usuario (opcional)
- `GET /api/security/logs/` - Logs globales
- `GET /api/minecraft/versions/` - Versiones globales

## Ventajas

1. ✅ **Stateless**: El servidor no mantiene estado del cliente
2. ✅ **RESTful**: Cada request es independiente
3. ✅ **Simple**: El cliente tiene control total
4. ✅ **Escalable**: Fácil de cachear, balancear, etc.
5. ✅ **Claro**: Es obvio qué servidor se está usando en cada request

## Plan de Migración

1. **Fase 1**: Agregar soporte para `X-Server-ID` header y query param en endpoints legacy
2. **Fase 2**: Documentar que el cliente debe enviar siempre `server_id`
3. **Fase 3**: Deprecar `switch_server` (marcar como obsoleto)
4. **Fase 4**: Migrar endpoints legacy a nueva estructura con `server_id` en URL
5. **Fase 5**: Eliminar lógica de detección automática (excepto dashboard)

