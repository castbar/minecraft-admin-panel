# Revisión de Seguridad - Datos Privados Expuestos

## ⚠️ PROBLEMAS ENCONTRADOS

### 1. **IP del Servidor Expuesta** 🔴 CRÍTICO
- **Ubicación**: Múltiples archivos en `test.http/`
- **IP**: `192.168.0.236`
- **Archivos afectados**:
  - `test.http/test_whitelist_add_real.py` (línea 27)
  - `test.http/test_all_real_server.sh` (línea 13)
  - `test.http/test_minecraft_versions_real_server.sh`
  - `test.http/test_backups_create_restore_real_server.sh`
  - `test.http/test_users_update_delete_real_server.sh`
  - `test.http/test_email_registration_real_server.sh`
  - `test.http/test_minecraft_users_real_server.sh`
  - `test.http/test_settings_update_real_server.sh`
  - `test.http/test_whitelist_remove_real_server.sh`
  - `test.http/test_whitelist_add_real_server.sh`

### 2. **Contraseña RCON Hardcodeada** 🔴 CRÍTICO
- **Archivo**: `test.http/test_whitelist_add_real.py`
- **Línea 30**: `RCON_PASSWORD = 'cobblemon123'`
- **Riesgo**: Exposición de credenciales de acceso al servidor Minecraft

### 3. **Usuario SSH Expuesto** 🟡 MEDIO
- **Usuario**: `carlitos@`
- **Ubicación**: Múltiples scripts de test y deploy
- **Archivos**:
  - `scripts/deploy-to-server.sh` (línea 17)
  - Todos los archivos en `test.http/`

### 4. **SECRET_KEY por Defecto** 🟡 MEDIO
- **Archivo**: `panel/minecraft_panel/settings.py`
- **Línea 14**: Tiene un valor por defecto inseguro
- **Nota**: Aunque usa variables de entorno, el valor por defecto es inseguro

### 5. **Contraseña de Ejemplo en Código** 🟢 BAJO
- **Archivo**: `panel/server/views/views_docker.py`
- **Línea 51**: `"rcon_password": "password123"` (solo es un ejemplo en documentación)

## ✅ BUENAS PRÁCTICAS ENCONTRADAS

1. ✅ `.env` está en `.gitignore` - Correcto
2. ✅ No hay archivos `.key`, `.pem`, `.secret` en el repo
3. ✅ Las contraseñas se obtienen de variables de entorno
4. ✅ El SECRET_KEY usa variables de entorno (aunque tiene fallback inseguro)

## 🔧 RECOMENDACIONES

### Acción Inmediata:
1. **Mover archivos de test a `.gitignore`** o crear una carpeta `.temp/` para tests locales
2. **Eliminar o sanitizar** la contraseña RCON de `test_whitelist_add_real.py`
3. **Reemplazar IPs hardcodeadas** con variables de entorno o archivos de configuración locales
4. **Eliminar el SECRET_KEY por defecto** y forzar que se use variable de entorno

### Archivos a Modificar:
- `test.http/test_whitelist_add_real.py` - Eliminar contraseña y IP
- Todos los archivos en `test.http/` - Reemplazar IPs con variables
- `panel/minecraft_panel/settings.py` - Eliminar SECRET_KEY por defecto

### Opciones:
1. **Opción A**: Agregar `test.http/` a `.gitignore` (si son solo para desarrollo local)
2. **Opción B**: Crear archivos de ejemplo sin datos reales (`test.http/*.example.sh`)
3. **Opción C**: Usar variables de entorno en todos los scripts de test

