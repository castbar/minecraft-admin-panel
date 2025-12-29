# Eliminación del Frontend Django - Migración a Ionic

## Resumen

Se ha eliminado completamente el frontend basado en templates Django y se ha configurado el sistema para servir únicamente el frontend Ionic compilado.

## Cambios Realizados

### 1. Templates Eliminados ✅

Se eliminaron todos los templates del panel Django:
- ❌ `panel/templates/panel/base.html`
- ❌ `panel/templates/panel/dashboard.html`
- ❌ `panel/templates/panel/mods.html`
- ❌ `panel/templates/panel/control.html`
- ❌ `panel/templates/panel/players.html`
- ❌ `panel/templates/panel/settings.html`
- ❌ `panel/templates/panel/logs.html`

**Mantenido:**
- ✅ `panel/templates/panel/login.html` - Necesario para autenticación Django

### 2. Vistas Eliminadas ✅

- ❌ `panel/server/views/views_pages.py` - Eliminado completamente
- ❌ Todas las funciones: `mods_page()`, `players_page()`, `logs_page()`, `control_page()`, `settings_page()`

### 3. Rutas Actualizadas ✅

**Eliminadas:**
- ❌ `/control/` - Página de control
- ❌ `/players/` - Página de jugadores
- ❌ `/mods/` - Página de mods
- ❌ `/settings/` - Página de configuración
- ❌ `/logs/` - Página de logs
- ❌ `/` - Dashboard Django

**Mantenidas:**
- ✅ `/login/` - Autenticación Django
- ✅ `/logout/` - Cerrar sesión
- ✅ `/api/*` - Todas las APIs (sin cambios)

**Nuevo comportamiento:**
- ✅ Todas las rutas que no sean `/api/*`, `/admin/*`, `/login/`, `/logout/`, `/static/*` se sirven desde `frontend/dist/index.html` (SPA routing)

### 4. Configuración de URLs ✅

**Antes:**
```python
# Páginas Django
path('control/', views_pages.control_page, ...)
path('players/', views_pages.players_page, ...)
# ... más páginas

# Fallback a dashboard Django si no hay frontend
path('', views.dashboard, name='dashboard')
```

**Después:**
```python
# Solo autenticación
path('login/', views_auth.LoggedLoginView.as_view(...), name='login'),
path('logout/', auth_views.LogoutView.as_view(), name='logout'),

# Servir frontend Ionic - todas las rutas no-API se sirven desde index.html
re_path(r'^(?!api|admin|static|media|login|logout|.*\.(css|js|...)).*$', serve, {
    'document_root': str(FRONTEND_DIST),
    'path': 'index.html'
})
```

### 5. Imports Actualizados ✅

**Eliminado:**
- ❌ `from server.views import views_pages`
- ❌ `from .views_pages import *` en `__init__.py`

**Agregado:**
- ✅ Imports de vistas de mods y configuraciones

## Estructura Actual

```
panel/
├── templates/
│   └── panel/
│       └── login.html          # ✅ Solo login Django
├── server/
│   └── views/
│       ├── views.py            # ✅ Dashboard (ya no se usa)
│       ├── views_api.py        # ✅ APIs
│       ├── views_auth.py       # ✅ Autenticación
│       ├── views_pages.py      # ❌ ELIMINADO
│       └── ...
└── minecraft_panel/
    └── urls.py                 # ✅ Configurado para servir Ionic
```

## Frontend Ionic

El frontend Ionic debe estar compilado en:
```
frontend/dist/
└── index.html                  # ✅ Punto de entrada SPA
```

### Configuración de Build

El frontend Ionic se compila con:
```bash
cd frontend
npm install
npm run build -- --configuration production
```

El output se guarda en `frontend/dist/` y Django lo sirve automáticamente.

## Flujo de Autenticación

1. Usuario accede a `/` → Django sirve `frontend/dist/index.html`
2. Frontend Ionic detecta que no está autenticado → Redirige a `/login/`
3. Usuario se autentica en `/login/` (template Django)
4. Django redirige a `/` después del login
5. Frontend Ionic carga y hace peticiones a `/api/*`

## APIs Disponibles

Todas las APIs siguen funcionando igual:
- ✅ `/api/servers/` - Listar servidores
- ✅ `/api/servers/<id>/status/` - Estado del servidor
- ✅ `/api/servers/<id>/mods/` - Gestión de mods
- ✅ `/api/mods/pool/` - Pool de mods
- ✅ ... todas las demás APIs

**Importante:** El frontend Ionic debe usar el header `X-Server-ID` para identificar el servidor en las peticiones API.

## Próximos Pasos

1. ✅ Frontend Django eliminado
2. ⏳ Frontend Ionic debe integrar las nuevas APIs
3. ⏳ Frontend Ionic debe usar header `X-Server-ID`
4. ⏳ Frontend Ionic debe manejar autenticación con sesiones Django

## Notas

- El template `login.html` se mantiene porque Django maneja la autenticación
- Todas las rutas del frontend Ionic funcionan con SPA routing
- Los archivos estáticos (CSS, JS, imágenes) se sirven automáticamente desde `frontend/dist/`
- Si no hay frontend compilado, se redirige a `/login/`

