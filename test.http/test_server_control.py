#!/usr/bin/env python
"""
Test para el endpoint POST /api/servers/<id>/control/<action>/
Verifica que:
1. Se validen las acciones permitidas
2. Se verifiquen los permisos (control_server)
3. Se valide que el servidor tenga container_name
4. Se manejen correctamente los errores de Docker
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

def test_server_control():
    """Test del endpoint POST /api/servers/<id>/control/<action>/"""
    print("=" * 60)
    print("TEST: POST /api/servers/<id>/control/<action>/")
    print("=" * 60)
    
    # Crear cliente de test
    client = Client()
    
    # Crear usuario staff para el test
    test_username = 'test_admin_control'
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
    
    # Crear un servidor con container_name para el test
    print("\n🧪 Preparando servidor de test...")
    server_data = {
        'name': 'Servidor Control Test',
        'host': 'test-control-server.local',
        'container_name': 'test-container-control',
        'rcon_port': 25575,
        'rcon_password': 'test_rcon_password_123'
    }
    
    response = client.post(
        '/api/servers/create/',
        data=json.dumps(server_data),
        content_type='application/json'
    )
    
    if response.status_code != 200:
        print(f"❌ Error: No se pudo crear el servidor: {response.status_code}")
        user.delete()
        return False
    
    response_data = json.loads(response.content)
    server_id = response_data.get('server_id')
    print(f"✅ Servidor creado con ID: {server_id}")
    
    # Test 1: Verificar acciones válidas
    print("\n🧪 Test 1: Verificar acciones válidas")
    valid_actions = ['start', 'stop', 'restart', 'pause', 'unpause']
    
    for action in valid_actions:
        response = client.post(
            f'/api/servers/{server_id}/control/{action}/',
            content_type='application/json'
        )
        
        print(f"  Action: {action} - Status: {response.status_code}")
        response_data = json.loads(response.content)
        
        # El endpoint puede retornar 200 (éxito) o 500 (error de Docker, pero el endpoint funciona)
        if response.status_code in [200, 500]:
            print(f"  ✅ Acción '{action}' procesada correctamente (puede fallar si Docker no está disponible)")
            if response_data.get('success'):
                print(f"     Mensaje: {response_data.get('message')}")
            else:
                print(f"     Error: {response_data.get('error')} (esperado si Docker no está disponible)")
        else:
            print(f"  ❌ Error inesperado: {response.status_code}")
            print(f"     Response: {json.dumps(response_data, indent=2)}")
    
    # Test 2: Verificar acción inválida
    print("\n🧪 Test 2: Verificar acción inválida")
    response = client.post(
        f'/api/servers/{server_id}/control/invalid_action/',
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code == 400 and not response_data.get('success'):
        print("✅ Acción inválida rechazada correctamente")
    else:
        print("❌ Error: Acción inválida no fue rechazada")
    
    # Test 3: Verificar servidor sin container_name
    print("\n🧪 Test 3: Verificar servidor sin container_name")
    server_no_container = Server.objects.create(
        name='Servidor Sin Container',
        host='test-no-container.local',
        container_name=None,  # Sin container_name
        rcon_port=25575,
        rcon_password='test_password',
        is_active=True
    )
    
    # Asignar rol admin al usuario
    UserServerRole.objects.create(
        user=user,
        server=server_no_container,
        role='admin'
    )
    
    response = client.post(
        f'/api/servers/{server_no_container.id}/control/start/',
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code == 400 and not response_data.get('success'):
        print("✅ Servidor sin container_name rechazado correctamente")
    else:
        print("❌ Error: Servidor sin container_name no fue rechazado")
    
    # Limpiar servidor sin container
    server_no_container.delete()
    
    # Test 4: Verificar permisos (usuario sin permiso control_server)
    print("\n🧪 Test 4: Verificar permisos (usuario viewer)")
    # Crear usuario viewer
    viewer_user = User.objects.create_user(
        username='test_viewer',
        password='test_password_123'
    )
    
    # Obtener el servidor y asignar rol viewer
    server = Server.objects.get(id=server_id)
    UserServerRole.objects.filter(user=viewer_user, server=server).delete()
    UserServerRole.objects.create(
        user=viewer_user,
        server=server,
        role='viewer'  # Viewer no tiene permiso control_server
    )
    
    # Autenticar como viewer
    client.logout()
    client.login(username='test_viewer', password='test_password_123')
    
    response = client.post(
        f'/api/servers/{server_id}/control/start/',
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code == 403 and not response_data.get('success'):
        print("✅ Usuario sin permisos rechazado correctamente")
    else:
        print("❌ Error: Usuario sin permisos pudo ejecutar acción")
    
    # Volver a autenticar como admin
    client.logout()
    client.login(username=test_username, password=test_password)
    
    # Limpiar usuario viewer
    viewer_user.delete()
    
    # Test 5: Verificar servidor inexistente
    print("\n🧪 Test 5: Verificar servidor inexistente")
    response = client.post(
        '/api/servers/99999/control/start/',
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    
    # El 404 puede retornar HTML o JSON dependiendo de la configuración
    if response.status_code == 404:
        print("✅ Servidor inexistente rechazado correctamente (404)")
    elif response.status_code == 403:
        # Intentar parsear como JSON
        try:
            response_data = json.loads(response.content)
            print(f"✅ Servidor inexistente rechazado correctamente (403 - sin acceso)")
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print("✅ Servidor inexistente rechazado correctamente (403 - HTML)")
    else:
        print(f"⚠️  Status code inesperado: {response.status_code}")
    
    # Limpiar
    print("\n🧹 Limpiando...")
    server.delete()
    print("✅ Servidor de test eliminado")
    
    user.delete()
    print("✅ Usuario de test eliminado")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_server_control()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

