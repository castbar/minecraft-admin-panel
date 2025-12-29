# Minecraft Admin Panel

Panel de administración web para servidores Minecraft desarrollado por Castbar.

## Características

- ✅ Gestión de múltiples servidores Minecraft
- ✅ Gestión de whitelist
- ✅ Gestión de mods
- ✅ Visualización de jugadores en tiempo real
- ✅ Visualización de logs
- ✅ Control del servidor (iniciar, detener, reiniciar)
- ✅ Configuración del servidor
- ✅ Sistema de roles y permisos
- ✅ Autenticación de usuarios de Minecraft vía base de datos
- ✅ Backups manuales y programados
- ✅ Sistema de notificaciones
- ✅ Métricas para Prometheus

## Requisitos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- Servidor Minecraft con RCON habilitado

## Instalación

1. Clonar el repositorio:
```bash
git clone git@github.com:castbar/minecraft-admin-panel.git
cd minecraft-admin-panel
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus valores
```

3. Construir y levantar:
```bash
docker compose up -d
```

4. Acceder al panel:
```
http://localhost:8000
```

## Configuración

Ver `.env.example` para todas las variables de entorno disponibles.

## Desarrollo

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r panel/requirements.txt

# Ejecutar migraciones
cd panel
python manage.py migrate

# Crear superusuario
python create_superuser.py

# Ejecutar servidor de desarrollo
python manage.py runserver
```

## Licencia

Copyright © Castbar. Todos los derechos reservados.

