#!/usr/bin/env python
"""
Test para verificar que después de crear un servidor:
1. Aparezca en la lista de servidores (GET /api/servers/)
2. Se pueda obtener su status (GET /api/servers/<id>/status/)
3. La información sea correcta
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panel'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from server.models import Server, UserServerRole

def test_server_list_and_status():
    """Test que verifica que el servidor creado aparezca en la lista y tenga status"""
    print("=" * 60)
    print("TEST: Servidor aparece en lista y tiene status")
    print("=" * 60)
    
    # Crear cliente de test
    client = Client()
    
    # Crear usuario staff para el test
    test_username = 'test_admin_list'
    test_password = 'test_password_123'
    
    # Eliminar usuario si existe
    User.objects.filter(username=test_username).delete()
    
    # Crear usuario staff
    user = User.objects.create_user(
        username=test_username,
        password=test_password,
        is_staff=True,
        is_superuser=False
    )
    print(f"✅ Usuario de test creado: {test_username}")
    
    # Autenticar
    login_success = client.login(username=test_username, password=test_password)
    if not login_success:
        print("❌ Error: No se pudo autenticar")
        return False
    print("✅ Autenticación exitosa")
    
    # Test 1: Verificar que inicialmente no hay servidores
    print("\n🧪 Test 1: Listar servidores (inicialmente vacío)")
    response = client.get('/api/servers/')
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Error: Se esperaba 200, se obtuvo {response.status_code}")
        user.delete()
        return False
    
    response_data = json.loads(response.content)
    initial_count = len(response_data.get('data', []))
    print(f"✅ Servidores iniciales: {initial_count}")
    
    # Test 2: Crear un servidor
    print("\n🧪 Test 2: Crear servidor")
    server_data = {
        'name': 'Servidor de Test Lista',
        'host': 'test-server-list.local',
        'rcon_port': 25575,
        'rcon_password': 'test_rcon_password_123'
    }
    
    response = client.post(
        '/api/servers/create/',
        data=json.dumps(server_data),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code != 200 or not response_data.get('success'):
        print(f"❌ Error: No se pudo crear el servidor")
        user.delete()
        return False
    
    server_id = response_data.get('server_id')
    print(f"✅ Servidor creado con ID: {server_id}")
    
    # Test 3: Verificar que el servidor aparece en la lista
    print("\n🧪 Test 3: Verificar que el servidor aparece en la lista")
    response = client.get('/api/servers/')
    
    if response.status_code != 200:
        print(f"❌ Error: Se esperaba 200, se obtuvo {response.status_code}")
        Server.objects.filter(id=server_id).delete()
        user.delete()
        return False
    
    response_data = json.loads(response.content)
    servers = response_data.get('data', [])
    print(f"✅ Total de servidores en lista: {len(servers)}")
    
    # Buscar el servidor creado en la lista
    server_found = None
    for server in servers:
        if server.get('id') == server_id:
            server_found = server
            break
    
    if not server_found:
        print(f"❌ Error: El servidor con ID {server_id} no aparece en la lista")
        print(f"Servidores en lista: {json.dumps(servers, indent=2)}")
        Server.objects.filter(id=server_id).delete()
        user.delete()
        return False
    
    print(f"✅ Servidor encontrado en la lista:")
    print(json.dumps(server_found, indent=2))
    
    # Verificar campos en la lista
    assert server_found.get('id') == server_id, "ID no coincide"
    assert server_found.get('name') == server_data['name'], f"Nombre no coincide: {server_found.get('name')} != {server_data['name']}"
    assert server_found.get('host') == server_data['host'], f"Host no coincide: {server_found.get('host')} != {server_data['host']}"
    assert server_found.get('role') == 'admin', f"Rol no es admin: {server_found.get('role')}"
    print("✅ Todos los campos en la lista son correctos")
    
    # Test 4: Obtener status del servidor
    print("\n🧪 Test 4: Obtener status del servidor")
    response = client.get(f'/api/servers/{server_id}/status/')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Error: Se esperaba 200, se obtuvo {response.status_code}")
        response_data = json.loads(response.content)
        print(f"Response: {json.dumps(response_data, indent=2)}")
        Server.objects.filter(id=server_id).delete()
        user.delete()
        return False
    
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if not response_data.get('success'):
        print(f"❌ Error: La respuesta indica fallo: {response_data.get('error')}")
        Server.objects.filter(id=server_id).delete()
        user.delete()
        return False
    
    status_data = response_data.get('data', {})
    
    # Verificar que el status tiene los campos esperados
    expected_fields = ['online', 'players', 'player_count', 'max_players', 'container_status']
    for field in expected_fields:
        if field not in status_data:
            print(f"⚠️  Campo '{field}' no está en la respuesta del status")
        else:
            print(f"✅ Campo '{field}': {status_data[field]}")
    
    # Verificar tipos de datos
    assert isinstance(status_data.get('online'), bool), "online debe ser boolean"
    assert isinstance(status_data.get('players'), list), "players debe ser lista"
    assert isinstance(status_data.get('player_count'), int), "player_count debe ser int"
    assert isinstance(status_data.get('max_players'), int), "max_players debe ser int"
    
    print("✅ Estructura del status es correcta")
    
    # Test 5: Verificar que el servidor aparece inmediatamente después de crearlo
    print("\n🧪 Test 5: Verificar que aparece inmediatamente (sin refresh)")
    response = client.get('/api/servers/')
    response_data = json.loads(response.content)
    servers_after = response_data.get('data', [])
    
    server_found_after = None
    for server in servers_after:
        if server.get('id') == server_id:
            server_found_after = server
            break
    
    if not server_found_after:
        print("❌ Error: El servidor no aparece inmediatamente después de crearlo")
        Server.objects.filter(id=server_id).delete()
        user.delete()
        return False
    
    print("✅ El servidor aparece inmediatamente en la lista")
    
    # Test 6: Verificar que el UserServerRole existe
    print("\n🧪 Test 6: Verificar UserServerRole")
    user_role = UserServerRole.objects.filter(user=user, server_id=server_id).first()
    
    if not user_role:
        print("❌ Error: UserServerRole no existe")
        Server.objects.filter(id=server_id).delete()
        user.delete()
        return False
    
    assert user_role.role == 'admin', f"Rol no es admin: {user_role.role}"
    assert user_role.server.id == server_id, "Server ID no coincide"
    print(f"✅ UserServerRole existe con rol: {user_role.role}")
    
    # Limpiar
    print("\n🧹 Limpiando...")
    Server.objects.filter(id=server_id).delete()
    print("✅ Servidor de test eliminado")
    
    user.delete()
    print("✅ Usuario de test eliminado")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_server_list_and_status()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

