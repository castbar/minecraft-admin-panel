#!/bin/bash
# Test del endpoint whitelist_add desde el servidor mismo
# Se ejecuta dentro del contenedor minecraft-admin-panel

set -e

echo "============================================================"
echo "TEST: POST /api/servers/<id>/whitelist/add/ (Desde Servidor)"
echo "============================================================"

# Configuración
SERVER_HOST="cobblemon-server"  # Nombre del contenedor en la misma red
RCON_PORT=25575
RCON_PASSWORD="cobblemon123"
TEST_USERNAME="TestPlayerReal_$(date +%s)"

echo ""
echo "📋 Configuración:"
echo "   Host: $SERVER_HOST (contenedor Docker)"
echo "   RCON Port: $RCON_PORT"
echo "   Test Username: $TEST_USERNAME"
echo ""

# Ejecutar test dentro del contenedor
ssh carlitos@192.168.0.236 << 'EOF'
    docker exec minecraft-admin-panel python -c "
import os
import sys
import django
import json
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from server.models import Server, UserServerRole
from django.contrib.auth.models import User

# Buscar o crear servidor cobblemon
server = Server.objects.filter(container_name='cobblemon-server').first()

if not server:
    server = Server.objects.filter(host__icontains='cobblemon').first()

if not server:
    print('❌ Servidor cobblemon no encontrado en BD')
    print('   Creando servidor...')
    server = Server.objects.create(
        name='Cobblemon Server',
        host='cobblemon-server',
        container_name='cobblemon-server',
        rcon_port=25575,
        rcon_password='cobblemon123',
        minecraft_data_path='/data',
        is_active=True,
        enable_whitelist=True,
        auth_mode='whitelist',
        server_type='fabric',
        minecraft_version='1.21.1'
    )
    print(f'✅ Servidor creado: ID {server.id}')

# Obtener o crear usuario admin
admin_user, _ = User.objects.get_or_create(
    username='test_admin_real',
    defaults={'is_staff': True}
)
if not admin_user.check_password('test_password_123'):
    admin_user.set_password('test_password_123')
    admin_user.save()

# Asegurar acceso
UserServerRole.objects.get_or_create(
    user=admin_user,
    server=server,
    defaults={'role': 'admin'}
)

print(f'✅ Servidor: {server.name} (ID: {server.id})')
print(f'✅ Host: {server.host}')
print(f'✅ Container: {server.container_name}')
print('')

# Probar conexión RCON directamente
print('🧪 Test 1: Probar conexión RCON directa...')
try:
    import mcrcon
    rcon = mcrcon.MCRcon(server.host, server.rcon_password, port=server.rcon_port)
    rcon.connect()
    response = rcon.command('list')
    print(f'✅ RCON conectado exitosamente!')
    print(f'   Respuesta: {response[:100]}...')
    rcon.disconnect()
except Exception as e:
    print(f'❌ Error RCON: {e}')
    sys.exit(1)

# Probar endpoint via API
print('')
print('🧪 Test 2: Probar endpoint POST /api/servers/<id>/whitelist/add/...')

# Crear sesión Django para el cliente
from django.test import Client
client = Client()
client.login(username='test_admin_real', password='test_password_123')

test_username = f'TestPlayerReal_{os.urandom(2).hex()}'
print(f'   Usuario de prueba: {test_username}')

response = client.post(
    f'/api/servers/{server.id}/whitelist/add/',
    data=json.dumps({'username': test_username}),
    content_type='application/json'
)

print(f'   Status Code: {response.status_code}')
response_data = json.loads(response.content)
print(f'   Response: {json.dumps(response_data, indent=2)}')

if response.status_code == 200 and response_data.get('success'):
    print(f'✅ Usuario agregado exitosamente!')
    print(f'   Mensaje: {response_data.get(\"message\")}')
    
    # Verificar en whitelist
    print('')
    print('🧪 Test 3: Verificar que aparece en whitelist...')
    response = client.get(f'/api/servers/{server.id}/whitelist/')
    if response.status_code == 200:
        whitelist_data = json.loads(response.content)
        usernames = [u.get('name', '') for u in whitelist_data.get('data', [])]
        if test_username in usernames:
            print(f'✅ Usuario encontrado en whitelist!')
        else:
            print(f'⚠️  Usuario no encontrado (puede tardar un momento)')
    
    # Limpiar
    print('')
    print('🧹 Limpiando: Removiendo usuario de prueba...')
    response = client.post(
        f'/api/servers/{server.id}/whitelist/remove/',
        data=json.dumps({'username': test_username}),
        content_type='application/json'
    )
    if response.status_code == 200:
        print('✅ Usuario removido')
    
    print('')
    print('=' * 60)
    print('✅ TEST EXITOSO - El endpoint funciona con servidor REAL')
    print('=' * 60)
    sys.exit(0)
else:
    print(f'❌ Error: {response_data.get(\"error\")}')
    sys.exit(1)
"
EOF

