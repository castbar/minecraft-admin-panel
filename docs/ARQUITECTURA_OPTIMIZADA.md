# Arquitectura Optimizada - Nginx + Django

## Resumen

Se ha optimizado la arquitectura para usar **Nginx para el frontend** y **Django solo para APIs**. Esta es la configuración más eficiente y escalable.

## Arquitectura Final

```
Usuario (Puerto 8080)
    ↓
Nginx (minecraft-admin-frontend)
    ├─ / → Frontend Ionic (index.html desde /usr/share/nginx/html/)
    ├─ /api/* → Proxy a Django (minecraft-admin-panel:8000)
    ├─ /admin/* → Proxy a Django
    └─ /login, /logout → Proxy a Django

Django (minecraft-admin-panel:8000)
    ├─ /api/* → APIs REST
    ├─ /admin/* → Admin Django
    └─ /login, /logout → Autenticación
```

## Cambios Realizados

### 1. ✅ Django Optimizado

**Antes:**
- Django servía frontend + APIs
- Copiaba frontend/dist/ al contenedor
- Usaba regex complejos para servir SPA

**Después:**
- Django solo sirve APIs y admin
- No necesita frontend compilado
- Código más simple y eficiente

**Archivos modificados:**
- `panel/Dockerfile` - Removida copia de frontend
- `panel/minecraft_panel/urls.py` - Removida lógica de servir frontend
- `panel/minecraft_panel/settings.py` - Removido FRONTEND_DIST de STATICFILES_DIRS

### 2. ✅ Nginx Configurado

**Archivos creados:**
- `frontend/nginx.conf` - Configuración completa de Nginx
- `frontend/Dockerfile` - Dockerfile optimizado para Nginx
- `frontend/.dockerignore` - Ignorar archivos innecesarios

**Características:**
- SPA routing con `try_files`
- Proxy a Django para `/api/*`, `/admin/*`, `/login`, `/logout`
- Cache para archivos estáticos con hash
- Compresión gzip
- Health check

### 3. ✅ Scripts de Build Optimizados

**Scripts actualizados:**
- `scripts/build-and-push.sh` - Solo backend Django
- `scripts/build-and-push-frontend.sh` - Frontend con validaciones
- `scripts/build-and-push-all.sh` - **NUEVO** - Construye ambos

**Mejoras:**
- Validación de archivos antes de build
- Verificación de compilación exitosa
- Mensajes informativos
- Manejo de errores

## Estructura de Carpetas

```
proyecto/
├── frontend/
│   ├── dist/              # Output de compilación Ionic
│   │   ├── index.html
│   │   ├── main.*.js
│   │   ├── polyfills.*.js
│   │   └── assets/
│   ├── Dockerfile         # Construye imagen Nginx
│   ├── nginx.conf         # Configuración Nginx
│   └── .dockerignore
│
├── panel/
│   ├── Dockerfile         # Construye imagen Django (sin frontend)
│   └── ...
│
└── scripts/
    ├── build-and-push.sh           # Backend
    ├── build-and-push-frontend.sh  # Frontend
    └── build-and-push-all.sh      # Ambos
```

## Proceso de Build

### Opción 1: Build Individual

```bash
# Solo frontend
./scripts/build-and-push-frontend.sh latest

# Solo backend
./scripts/build-and-push.sh latest
```

### Opción 2: Build Completo (RECOMENDADO)

```bash
# Construye y publica ambos
./scripts/build-and-push-all.sh latest
```

### Proceso Interno

1. **Frontend:**
   ```bash
   cd frontend
   npm install --legacy-peer-deps
   npm run build -- --configuration production --base-href=/
   # Verifica que dist/index.html existe
   docker buildx build -f frontend/Dockerfile frontend/ --push
   ```

2. **Backend:**
   ```bash
   docker buildx build -f panel/Dockerfile . --push
   # Contexto es raíz del proyecto
   # Copia panel/ al contenedor
   ```

## Configuración de Ionic

### angular.json

```json
{
  "projects": {
    "app": {
      "architect": {
        "build": {
          "options": {
            "baseHref": "/",
            "outputPath": "dist",
            "deployUrl": "/"
          }
        }
      }
    }
  }
}
```

### Compilación

```bash
# Desde frontend/
ionic build --prod
# O
ng build --configuration production --base-href=/
```

## Docker Compose

El `docker-compose.yml` ya está configurado correctamente:

```yaml
services:
  minecraft-admin-frontend:  # Nginx - Puerto 8080
    image: registry.castbar.dev/castbar/minecraft-admin-frontend:latest
    ports:
      - "8080:80"
    depends_on:
      - minecraft-admin-panel

  minecraft-admin-panel:  # Django - Puerto 8000 (interno)
    image: registry.castbar.dev/castbar/minecraft-admin-panel:latest
    expose:
      - "8000"
```

## Ventajas de esta Arquitectura

1. ✅ **Rendimiento**: Nginx es más eficiente para archivos estáticos
2. ✅ **Separación**: Frontend y backend independientes
3. ✅ **Escalabilidad**: Puedes escalar frontend y backend por separado
4. ✅ **Cache**: Nginx puede cachear archivos estáticos eficientemente
5. ✅ **Simplicidad**: Django solo maneja APIs, código más limpio
6. ✅ **Deploy**: Puedes actualizar frontend sin tocar backend

## Verificación

### 1. Verificar Frontend

```bash
# Construir frontend
./scripts/build-and-push-frontend.sh test

# Verificar que la imagen tiene index.html
docker run --rm registry.castbar.dev/castbar/minecraft-admin-frontend:test \
  ls -la /usr/share/nginx/html/
```

### 2. Verificar Backend

```bash
# Construir backend
./scripts/build-and-push.sh test

# Verificar que no tiene frontend
docker run --rm registry.castbar.dev/castbar/minecraft-admin-panel:test \
  ls -la /app/ | grep frontend
# No debe aparecer frontend
```

### 3. Probar Localmente

```bash
# Levantar servicios
docker-compose up -d

# Verificar frontend
curl http://localhost:8080/
# Debe retornar index.html

# Verificar API
curl http://localhost:8080/api/servers/
# Debe hacer proxy a Django
```

## Troubleshooting

### Frontend no carga

1. Verificar que `dist/index.html` existe después de compilar
2. Verificar que `nginx.conf` está correcto
3. Verificar logs de Nginx: `docker logs minecraft-admin-frontend`

### API no funciona

1. Verificar que Django está corriendo: `docker logs minecraft-admin-panel`
2. Verificar proxy en `nginx.conf`
3. Verificar que el servicio se llama `minecraft-admin-panel` en docker-compose

### Rutas SPA no funcionan

1. Verificar `try_files` en `nginx.conf`
2. Verificar `baseHref` en `angular.json`
3. Verificar que se usa `PathLocationStrategy` en Ionic

## Próximos Pasos

1. ✅ Arquitectura optimizada
2. ✅ Scripts de build mejorados
3. ✅ Nginx configurado
4. ⏳ Compilar frontend Ionic con `baseHref` correcto
5. ⏳ Probar en producción
6. ⏳ Configurar HTTPS (si es necesario)

