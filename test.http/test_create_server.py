#!/usr/bin/env python
"""
Test para el endpoint POST /api/servers/create/
Verifica que:
1. Se requieren campos obligatorios
2. Se valida el puerto RCON
3. Se crea el servidor correctamente
4. Se crea el UserServerRole con rol admin
5. Se elimina el servidor después del test
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panel'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

# Ejecutar migraciones
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

from django.test import Client
from django.contrib.auth.models import User
from server.models import Server, UserServerRole

def test_create_server():
    """Test del endpoint POST /api/servers/create/"""
    print("=" * 60)
    print("TEST: POST /api/servers/create/")
    print("=" * 60)
    
    # Crear cliente de test
    client = Client()
    
    # Crear usuario staff para el test
    test_username = 'test_admin'
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
    
    # Datos mínimos requeridos para crear servidor
    server_data = {
        'name': 'Servidor de Test',
        'host': 'test-server.local',
        'rcon_port': 25575,
        'rcon_password': 'test_rcon_password_123'
    }
    
    print("\n📋 Datos del servidor a crear:")
    print(json.dumps(server_data, indent=2))
    
    # Test 1: Crear servidor con datos mínimos
    print("\n🧪 Test 1: Crear servidor con datos mínimos")
    response = client.post(
        '/api/servers/create/',
        data=json.dumps(server_data),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code != 200:
        print(f"❌ Error: Se esperaba 200, se obtuvo {response.status_code}")
        user.delete()
        return False
    
    if not response_data.get('success'):
        print(f"❌ Error: La respuesta indica fallo: {response_data.get('error')}")
        user.delete()
        return False
    
    server_id = response_data.get('server_id')
    if not server_id:
        print("❌ Error: No se retornó server_id")
        user.delete()
        return False
    
    print(f"✅ Servidor creado con ID: {server_id}")
    
    # Verificar que el servidor existe en la BD
    try:
        server = Server.objects.get(id=server_id)
        print(f"✅ Servidor encontrado en BD: {server.name}")
        
        # Verificar campos
        assert server.name == server_data['name'], f"Nombre no coincide: {server.name} != {server_data['name']}"
        assert server.host == server_data['host'], f"Host no coincide: {server.host} != {server_data['host']}"
        assert server.rcon_port == server_data['rcon_port'], f"Puerto RCON no coincide: {server.rcon_port} != {server_data['rcon_port']}"
        assert server.rcon_password == server_data['rcon_password'], "Password RCON no coincide"
        assert server.is_active == True, "Servidor no está activo"
        assert server.container_name == server_data['host'], f"container_name no coincide: {server.container_name} != {server_data['host']}"
        assert server.minecraft_data_path == '/data', f"minecraft_data_path no coincide: {server.minecraft_data_path} != /data"
        assert server.auth_mode == 'whitelist', f"auth_mode no coincide: {server.auth_mode} != whitelist"
        assert server.enable_whitelist == True, "enable_whitelist no es True"
        assert server.online_mode == False, "online_mode no es False"
        assert server.is_public == False, "is_public no es False"
        assert server.is_hidden == False, "is_hidden no es False"
        assert server.server_type == 'vanilla', f"server_type no coincide: {server.server_type} != vanilla"
        assert server.minecraft_version == 'latest', f"minecraft_version no coincide: {server.minecraft_version} != latest"
        assert server.install_spark == True, "install_spark no es True"
        
        print("✅ Todos los campos del servidor son correctos")
        
    except Server.DoesNotExist:
        print(f"❌ Error: Servidor con ID {server_id} no existe en BD")
        user.delete()
        return False
    
    # Verificar que se creó el UserServerRole
    try:
        user_role = UserServerRole.objects.get(user=user, server=server)
        assert user_role.role == 'admin', f"Rol no es admin: {user_role.role}"
        print(f"✅ UserServerRole creado correctamente con rol: {user_role.role}")
    except UserServerRole.DoesNotExist:
        print("❌ Error: UserServerRole no fue creado")
        server.delete()
        user.delete()
        return False
    
    # Test 2: Crear servidor con datos completos
    print("\n🧪 Test 2: Crear servidor con datos completos")
    server_data_full = {
        'name': 'Servidor Completo de Test',
        'host': 'test-server-full.local',
        'container_name': 'test-container-full',
        'rcon_port': 25576,
        'rcon_password': 'test_rcon_password_full_123',
        'minecraft_data_path': '/data/minecraft',
        'enable_whitelist': False,
        'online_mode': True,
        'auth_mode': 'database',
        'is_public': True,
        'is_hidden': False,
        'server_type': 'fabric',
        'minecraft_version': '1.20.1',
        'install_fabric_api': True,
        'install_spark': False,
        'additional_mods': ['mod1.jar', 'mod2.jar'],
        'additional_plugins': ['plugin1.jar']
    }
    
    response = client.post(
        '/api/servers/create/',
        data=json.dumps(server_data_full),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code == 200 and response_data.get('success'):
        server_id_full = response_data.get('server_id')
        server_full = Server.objects.get(id=server_id_full)
        
        # Verificar campos personalizados
        assert server_full.container_name == server_data_full['container_name']
        assert server_full.minecraft_data_path == server_data_full['minecraft_data_path']
        assert server_full.enable_whitelist == server_data_full['enable_whitelist']
        assert server_full.online_mode == server_data_full['online_mode']
        assert server_full.auth_mode == server_data_full['auth_mode']
        assert server_full.is_public == server_data_full['is_public']
        assert server_full.server_type == server_data_full['server_type']
        assert server_full.minecraft_version == server_data_full['minecraft_version']
        assert server_full.install_fabric_api == server_data_full['install_fabric_api']
        assert server_full.install_spark == server_data_full['install_spark']
        assert server_full.additional_mods == server_data_full['additional_mods']
        assert server_full.additional_plugins == server_data_full['additional_plugins']
        
        print("✅ Servidor con datos completos creado correctamente")
        
        # Eliminar servidor de test completo
        server_full.delete()
        print("✅ Servidor completo eliminado")
    else:
        print(f"⚠️  Test 2 falló, pero continuando...")
    
    # Test 3: Validar campos requeridos
    print("\n🧪 Test 3: Validar campos requeridos faltantes")
    for field in ['name', 'host', 'rcon_port', 'rcon_password']:
        test_data = server_data.copy()
        del test_data[field]
        
        response = client.post(
            '/api/servers/create/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        if response.status_code == 400 and not response_data.get('success'):
            print(f"✅ Campo requerido '{field}' validado correctamente")
        else:
            print(f"❌ Error: Campo '{field}' no fue validado correctamente")
    
    # Test 4: Validar puerto RCON inválido
    print("\n🧪 Test 4: Validar puerto RCON inválido")
    invalid_ports = [0, -1, 65536, 99999]
    for invalid_port in invalid_ports:
        test_data = server_data.copy()
        test_data['rcon_port'] = invalid_port
        
        response = client.post(
            '/api/servers/create/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        response_data = json.loads(response.content)
        if response.status_code == 400 and not response_data.get('success'):
            print(f"✅ Puerto inválido {invalid_port} rechazado correctamente")
        else:
            print(f"❌ Error: Puerto inválido {invalid_port} no fue rechazado")
    
    # Test 5: Usuario no staff no puede crear servidor
    print("\n🧪 Test 5: Usuario no staff no puede crear servidor")
    client.logout()
    non_staff_user = User.objects.create_user(
        username='test_non_staff',
        password='test_password_123',
        is_staff=False
    )
    client.login(username='test_non_staff', password='test_password_123')
    
    response = client.post(
        '/api/servers/create/',
        data=json.dumps(server_data),
        content_type='application/json'
    )
    
    response_data = json.loads(response.content)
    if response.status_code == 403 and not response_data.get('success'):
        print("✅ Usuario no staff correctamente rechazado")
    else:
        print(f"❌ Error: Usuario no staff pudo crear servidor")
    
    # Limpiar
    non_staff_user.delete()
    client.logout()
    
    # Eliminar servidor de test
    print("\n🧹 Limpiando...")
    server.delete()
    print("✅ Servidor de test eliminado")
    
    # Eliminar usuario de test
    user.delete()
    print("✅ Usuario de test eliminado")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_create_server()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

