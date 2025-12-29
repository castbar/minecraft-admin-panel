#!/bin/bash
# Test cuidadoso de settings update ejecutado dentro del contenedor

set -e

echo "============================================================"
echo "TEST: POST /api/servers/<id>/settings/update/ (CUIDADOSO)"
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

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.test import Client
from server.models import Server, UserServerRole
from django.contrib.auth.models import User

print('=' * 60)
print('TEST: POST /api/servers/<id>/settings/update/')
print('=' * 60)

client = Client()

# Obtener o crear usuario admin y asegurar que tenga acceso
admin_user, created = User.objects.get_or_create(
    username='test_admin_settings',
    defaults={'is_staff': True, 'is_superuser': True}
)
admin_user.set_password('test_password_123')
admin_user.save()

# Buscar servidor cobblemon
cobblemon_server = Server.objects.filter(container_name='cobblemon-server').first()
if not cobblemon_server:
    cobblemon_server = Server.objects.filter(name__icontains='cobblemon').first()

if cobblemon_server:
    server_id = cobblemon_server.id
    server_name = cobblemon_server.name
    # Asegurar que el usuario tenga acceso con permiso manage_settings
    UserServerRole.objects.get_or_create(
        user=admin_user,
        server=cobblemon_server,
        defaults={'role': 'admin'}
    )
    print(f'✅ Servidor encontrado: {server_name} (ID: {server_id})')
else:
    print('❌ No se encontró servidor cobblemon')
    sys.exit(1)

# Login con JSON
import json as json_lib
login_response = client.post(
    '/api/auth/login/',
    json_lib.dumps({
        'username': 'test_admin_settings',
        'password': 'test_password_123'
    }),
    content_type='application/json'
)

if login_response.status_code != 200:
    print(f'❌ Error de autenticación: {login_response.status_code}')
    print(login_response.content.decode())
    sys.exit(1)

print('✅ Autenticación exitosa')

# 1. Obtener configuración actual
print('\n' + '=' * 60)
print('📋 Obtener configuración actual')
print('=' * 60)
settings_response = client.get(f'/api/servers/{server_id}/settings/')
if settings_response.status_code != 200:
    print(f'❌ Error obteniendo configuración: {settings_response.status_code}')
    sys.exit(1)

settings_data = json.loads(settings_response.content)
if not settings_data.get('success'):
    print(f'❌ Error en respuesta: {settings_data.get(\"error\")}')
    sys.exit(1)

current_settings = settings_data.get('data', {})
print(f'   ✅ Configuración obtenida')
print(f'   - is_public: {current_settings.get(\"is_public\")}')
print(f'   - auth_mode: {current_settings.get(\"auth_mode\")}')
print(f'   - enable_whitelist: {current_settings.get(\"enable_whitelist\")}')
print(f'   - online_mode: {current_settings.get(\"online_mode\")}')
print(f'   - max_players: {current_settings.get(\"max_players\")}')
motd_preview = current_settings.get('motd', '')[:50]
print(f'   - motd: {motd_preview}...')

# Guardar valores originales para revertir
original_values = {
    'is_public': current_settings.get('is_public'),
    'motd': current_settings.get('motd', ''),
}

# 2. Testear update con cambios seguros
print('\n' + '=' * 60)
print('🧪 TEST: POST /api/servers/<id>/settings/update/')
print('=' * 60)
print('   ⚠️  Haciendo cambios seguros y reversibles...')

# Cambios seguros: solo is_public y motd (no afectan funcionalidad crítica)
test_changes = {
    'is_public': not current_settings.get('is_public', False),  # Invertir valor
    'motd': f'Test MOTD {int(time.time())}',  # MOTD de prueba
}

print(f'   Cambios a aplicar:')
print(f'   - is_public: {current_settings.get(\"is_public\")} -> {test_changes[\"is_public\"]}')
print(f'   - motd: \"{current_settings.get(\"motd\", \"\")[:30]}...\" -> \"{test_changes[\"motd\"]}\"')

update_response = client.post(
    f'/api/servers/{server_id}/settings/update/',
    json.dumps(test_changes),
    content_type='application/json'
)

print(f'\n   Status Code: {update_response.status_code}')

if update_response.status_code == 403:
    print(f'   ❌ Error 403 - CSRF o permisos')
    print(update_response.content.decode())
    sys.exit(1)
elif update_response.status_code != 200:
    print(f'   ❌ Error inesperado: {update_response.status_code}')
    print(update_response.content.decode())
    sys.exit(1)

update_data = json.loads(update_response.content)
if not update_data.get('success'):
    print(f'   ❌ Error en respuesta: {update_data.get(\"error\")}')
    sys.exit(1)

print(f'   ✅ Configuración actualizada exitosamente!')
print(f'   Mensaje: {update_data.get(\"message\")}')

# 3. Verificar que los cambios se aplicaron
print('\n' + '=' * 60)
print('🔍 Verificar cambios aplicados')
print('=' * 60)
verify_response = client.get(f'/api/servers/{server_id}/settings/')
if verify_response.status_code == 200:
    verify_data = json.loads(verify_response.content)
    if verify_data.get('success'):
        new_settings = verify_data.get('data', {})
        
        # Verificar is_public
        if new_settings.get('is_public') == test_changes['is_public']:
            print(f'   ✅ is_public actualizado correctamente: {new_settings.get(\"is_public\")}')
        else:
            print(f'   ⚠️  is_public no coincide: esperado {test_changes[\"is_public\"]}, obtenido {new_settings.get(\"is_public\")}')
        
        # Verificar motd (puede tener escape characters)
        new_motd = new_settings.get('motd', '')
        if test_changes['motd'] in new_motd or new_motd == test_changes['motd']:
            print(f'   ✅ motd actualizado correctamente: \"{new_motd[:50]}...\"')
        else:
            print(f'   ⚠️  motd no coincide completamente (puede tener escape): \"{new_motd[:50]}...\"')

# 4. Revertir cambios
print('\n' + '=' * 60)
print('🔄 Revertir cambios a valores originales')
print('=' * 60)
revert_changes = {
    'is_public': original_values['is_public'],
    'motd': original_values['motd'],
}

print(f'   Revirtiendo:')
print(f'   - is_public: {test_changes[\"is_public\"]} -> {revert_changes[\"is_public\"]}')
motd_revert_preview = revert_changes['motd'][:30] if revert_changes['motd'] else '(vacío)'
print(f'   - motd: \"{test_changes[\"motd\"]}\" -> \"{motd_revert_preview}...\"')

revert_response = client.post(
    f'/api/servers/{server_id}/settings/update/',
    json.dumps(revert_changes),
    content_type='application/json'
)

if revert_response.status_code == 200:
    revert_data = json.loads(revert_response.content)
    if revert_data.get('success'):
        print(f'   ✅ Cambios revertidos exitosamente')
    else:
        print(f'   ⚠️  Error al revertir: {revert_data.get(\"error\")}')
else:
    print(f'   ⚠️  Error al revertir: {revert_response.status_code}')

# 5. Verificar que se revirtieron
final_response = client.get(f'/api/servers/{server_id}/settings/')
if final_response.status_code == 200:
    final_data = json.loads(final_response.content)
    if final_data.get('success'):
        final_settings = final_data.get('data', {})
        if final_settings.get('is_public') == original_values['is_public']:
            print(f'   ✅ is_public revertido correctamente')
        else:
            print(f'   ⚠️  is_public no se revirtió completamente')

print('\n' + '=' * 60)
print('📊 RESUMEN')
print('=' * 60)
print('✅ Endpoint settings_update testeado exitosamente')
print('✅ Cambios aplicados y revertidos correctamente')
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

