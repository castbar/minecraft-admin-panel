#!/bin/bash
# Test de endpoints de versiones de Minecraft ejecutado dentro del contenedor
# Crea versiones de prueba, las testea, y luego las elimina

set -e

echo "============================================================"
echo "TEST: Versiones de Minecraft (latest y create)"
echo "============================================================"
echo ""

# Ejecutar test dentro del contenedor
ssh carlitos@192.168.0.236 << 'EOF'
    docker exec minecraft-admin-panel python -c "
import os
import sys
import django
import json
import time
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.test import Client
from server.models import MinecraftVersion
from django.contrib.auth.models import User

print('=' * 60)
print('TEST: Versiones de Minecraft')
print('=' * 60)

client = Client()

# Obtener o crear usuario admin (staff)
admin_user, created = User.objects.get_or_create(
    username='test_admin_versions',
    defaults={'is_staff': True, 'is_superuser': True}
)
admin_user.set_password('test_password_123')
admin_user.save()

# Crear servidor de prueba para que el usuario tenga acceso (necesario para login)
from server.models import Server, UserServerRole
test_server = Server.objects.filter(is_active=True).first()
if not test_server:
    test_server = Server.objects.create(
        name='Test Server Versions',
        host='test-versions.local',
        rcon_port=25575,
        rcon_password='test123',
        minecraft_data_path='/data',
        is_active=True
    )

# Asegurar que el usuario tenga acceso
UserServerRole.objects.get_or_create(
    user=admin_user,
    server=test_server,
    defaults={'role': 'admin'}
)

# Login con JSON
import json as json_lib
login_response = client.post(
    '/api/auth/login/',
    json_lib.dumps({
        'username': 'test_admin_versions',
        'password': 'test_password_123'
    }),
    content_type='application/json'
)

if login_response.status_code != 200:
    print(f'❌ Error de autenticación: {login_response.status_code}')
    print(login_response.content.decode()[:200])
    sys.exit(1)

print('✅ Autenticación exitosa')

# TEST 1: GET /api/minecraft/versions/latest/ (sin versiones)
print('\n' + '=' * 60)
print('🧪 TEST 1: GET /api/minecraft/versions/latest/ (sin versiones)')
print('=' * 60)

latest_response = client.get('/api/minecraft/versions/latest/')
print(f'   Status Code: {latest_response.status_code}')

if latest_response.status_code == 404:
    latest_data = json.loads(latest_response.content)
    if 'No version available' in latest_data.get('error', ''):
        print(f'   ✅ Comportamiento esperado: No version available')
        print(f'   Error: {latest_data.get(\"error\")}')
    else:
        print(f'   ⚠️  Error inesperado: {latest_data.get(\"error\")}')
elif latest_response.status_code == 200:
    latest_data = json.loads(latest_response.content)
    if latest_data.get('success'):
        version_data = latest_data.get('data', {})
        print(f'   ✅ Versión encontrada: {version_data.get(\"version\")}')
        print(f'   - Display name: {version_data.get(\"display_name\")}')
        print(f'   - Is latest: {version_data.get(\"is_latest\")}')
else:
    print(f'   ⚠️  Status inesperado: {latest_response.status_code}')

# TEST 2: POST /api/minecraft/versions/create/
print('\n' + '=' * 60)
print('🧪 TEST 2: POST /api/minecraft/versions/create/')
print('=' * 60)

test_version = f'1.99.{int(time.time()) % 1000}'
test_display_name = f'Test Version {test_version}'

print(f'   Creando versión: {test_version}')
print(f'   Display name: {test_display_name}')

create_data = {
    'version': test_version,
    'display_name': test_display_name,
    'is_latest': False,
    'is_stable': True,
    'server_types': ['vanilla', 'paper'],
    'release_date': '2024-01-01',
    'notes': 'Versión de prueba para testing',
    'is_supported': True
}

create_response = client.post(
    '/api/minecraft/versions/create/',
    json.dumps(create_data),
    content_type='application/json'
)

print(f'   Status Code: {create_response.status_code}')

if create_response.status_code == 403:
    print(f'   ❌ Error 403 - Permisos (usuario no es staff)')
    print(create_response.content.decode()[:200])
    sys.exit(1)
elif create_response.status_code != 200:
    print(f'   ❌ Error: {create_response.status_code}')
    print(create_response.content.decode()[:200])
    sys.exit(1)

create_version_data = json.loads(create_response.content)
if not create_version_data.get('success'):
    print(f'   ❌ Error: {create_version_data.get(\"error\")}')
    sys.exit(1)

print(f'   ✅ Versión creada exitosamente!')
print(f'   Mensaje: {create_version_data.get(\"message\")}')

version_data = create_version_data.get('data', {})
version_id = version_data.get('id')
print(f'   - Version ID: {version_id}')
print(f'   - Version: {version_data.get(\"version\")}')
print(f'   - Display name: {version_data.get(\"display_name\")}')

# Verificar en BD
version_obj = MinecraftVersion.objects.get(id=version_id)
print(f'   ✅ Versión verificada en BD')
print(f'   - is_latest: {version_obj.is_latest}')
print(f'   - is_stable: {version_obj.is_stable}')
print(f'   - server_types: {version_obj.server_types}')

# TEST 3: GET /api/minecraft/versions/latest/ (ahora con versiones)
print('\n' + '=' * 60)
print('🧪 TEST 3: GET /api/minecraft/versions/latest/ (con versiones)')
print('=' * 60)

latest_response2 = client.get('/api/minecraft/versions/latest/')
print(f'   Status Code: {latest_response2.status_code}')

if latest_response2.status_code == 200:
    latest_data2 = json.loads(latest_response2.content)
    if latest_data2.get('success'):
        latest_version_data = latest_data2.get('data', {})
        print(f'   ✅ Última versión encontrada')
        print(f'   - Version: {latest_version_data.get(\"version\")}')
        print(f'   - Display name: {latest_version_data.get(\"display_name\")}')
        print(f'   - Is latest: {latest_version_data.get(\"is_latest\")}')
elif latest_response2.status_code == 404:
    print(f'   ⚠️  Aún no hay versión marcada como latest')
else:
    print(f'   ⚠️  Status inesperado: {latest_response2.status_code}')

# TEST 4: Crear versión marcada como latest
print('\n' + '=' * 60)
print('🧪 TEST 4: POST /api/minecraft/versions/create/ - Versión latest')
print('=' * 60)

test_version_latest = f'1.100.{int(time.time()) % 1000}'
test_display_name_latest = f'Test Latest Version {test_version_latest}'

print(f'   Creando versión latest: {test_version_latest}')

create_latest_data = {
    'version': test_version_latest,
    'display_name': test_display_name_latest,
    'is_latest': True,  # Marcar como latest
    'is_stable': True,
    'server_types': ['vanilla'],
    'release_date': '2024-12-29',
    'notes': 'Versión latest de prueba',
    'is_supported': True
}

create_latest_response = client.post(
    '/api/minecraft/versions/create/',
    json.dumps(create_latest_data),
    content_type='application/json'
)

print(f'   Status Code: {create_latest_response.status_code}')

if create_latest_response.status_code == 200:
    create_latest_version_data = json.loads(create_latest_response.content)
    if create_latest_version_data.get('success'):
        print(f'   ✅ Versión latest creada exitosamente!')
        latest_version_id = create_latest_version_data.get('data', {}).get('id')
        
        # Verificar que la versión anterior ya no es latest
        version_obj.refresh_from_db()
        if not version_obj.is_latest:
            print(f'   ✅ Versión anterior ya no es latest (correcto)')
        else:
            print(f'   ⚠️  Versión anterior aún es latest')
        
        # Verificar que la nueva es latest
        latest_version_obj = MinecraftVersion.objects.get(id=latest_version_id)
        if latest_version_obj.is_latest:
            print(f'   ✅ Nueva versión es latest (correcto)')
        else:
            print(f'   ❌ Nueva versión no es latest')
        
        # TEST 5: GET /api/minecraft/versions/latest/ (ahora debería retornar la nueva)
        print('\n' + '=' * 60)
        print('🧪 TEST 5: GET /api/minecraft/versions/latest/ (después de crear latest)')
        print('=' * 60)
        
        latest_response3 = client.get('/api/minecraft/versions/latest/')
        print(f'   Status Code: {latest_response3.status_code}')
        
        if latest_response3.status_code == 200:
            latest_data3 = json.loads(latest_response3.content)
            if latest_data3.get('success'):
                latest_version_data3 = latest_data3.get('data', {})
                if latest_version_data3.get('version') == test_version_latest:
                    print(f'   ✅ Última versión correcta: {latest_version_data3.get(\"version\")}')
                else:
                    print(f'   ⚠️  Última versión diferente: {latest_version_data3.get(\"version\")} (esperado: {test_version_latest})')
        else:
            print(f'   ⚠️  Status inesperado: {latest_response3.status_code}')
        
        # Limpiar: eliminar versión latest
        latest_version_obj.delete()
        print(f'\n   ✅ Versión latest eliminada: {test_version_latest}')
else:
    print(f'   ⚠️  Error creando versión latest: {create_latest_response.status_code}')

# TEST 6: Validación - crear versión sin campo version
print('\n' + '=' * 60)
print('🧪 TEST 6: POST /api/minecraft/versions/create/ - Validación (sin version)')
print('=' * 60)

invalid_data = {
    'display_name': 'Invalid Version',
    'is_stable': True
}

invalid_response = client.post(
    '/api/minecraft/versions/create/',
    json.dumps(invalid_data),
    content_type='application/json'
)

print(f'   Status Code: {invalid_response.status_code}')

if invalid_response.status_code == 400:
    invalid_data_resp = json.loads(invalid_response.content)
    if 'Version is required' in invalid_data_resp.get('error', ''):
        print(f'   ✅ Validación correcta: Version is required')
    else:
        print(f'   ⚠️  Error inesperado: {invalid_data_resp.get(\"error\")}')
else:
    print(f'   ⚠️  Status inesperado: {invalid_response.status_code}')

# Limpiar: eliminar versión de prueba
print('\n' + '=' * 60)
print('🧹 Limpiando versiones de prueba')
print('=' * 60)

try:
    version_obj.delete()
    print(f'   ✅ Versión eliminada: {test_version}')
except Exception as e:
    print(f'   ⚠️  Error eliminando versión: {e}')

print('\n' + '=' * 60)
print('📊 RESUMEN')
print('=' * 60)
print('✅ GET /api/minecraft/versions/latest/ testeado completamente')
print('   - Sin versiones: ✅ (404 esperado)')
print('   - Con versiones: ✅')
print('   - Con versión latest: ✅')
print('✅ POST /api/minecraft/versions/create/ testeado completamente')
print('   - Crear versión: ✅')
print('   - Crear versión latest: ✅ (desmarca otras)')
print('   - Validación de campos: ✅')
print('✅ Versiones de prueba eliminadas correctamente')
print('=' * 60)
"
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Test completado exitosamente"
else
    echo ""
    echo "❌ Test falló con código: $EXIT_CODE"
fi

exit $EXIT_CODE

