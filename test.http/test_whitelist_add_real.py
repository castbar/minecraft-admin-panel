#!/usr/bin/env python
"""
Test para el endpoint POST /api/servers/<id>/whitelist/add/ con servidor REAL
Usa el servidor cobblemon real para probar que funciona con RCON
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

def test_whitelist_add_real():
    """Test del endpoint con servidor REAL cobblemon"""
    print("=" * 60)
    print("TEST: POST /api/servers/<id>/whitelist/add/ (Servidor REAL)")
    print("=" * 60)
    
    # Configuración del servidor real cobblemon
    SERVER_HOST = '192.168.0.236'  # IP del servidor
    SERVER_CONTAINER = 'cobblemon-server'
    RCON_PORT = 25575
    RCON_PASSWORD = 'cobblemon123'
    
    print(f"\n📋 Configuración del servidor real:")
    print(f"   Host: {SERVER_HOST}")
    print(f"   Container: {SERVER_CONTAINER}")
    print(f"   RCON Port: {RCON_PORT}")
    print(f"   RCON Password: {'*' * len(RCON_PASSWORD)}")
    
    # Crear cliente de test
    client = Client()
    
    # Obtener o crear usuario admin
    admin_user, created = User.objects.get_or_create(
        username='test_admin_real_whitelist',
        defaults={'is_staff': True, 'is_superuser': False}
    )
    if created:
        admin_user.set_password('test_password_123')
        admin_user.save()
        print(f"\n✅ Usuario de test creado: test_admin_real_whitelist")
    else:
        print(f"\n✅ Usuario de test existente: test_admin_real_whitelist")
    
    # Buscar o crear servidor cobblemon
    server = Server.objects.filter(host__icontains='192.168.0.236').first()
    
    if not server:
        # Buscar por container_name
        server = Server.objects.filter(container_name='cobblemon-server').first()
    
    if not server:
        # Crear servidor cobblemon
        print("\n🧪 Creando servidor cobblemon en la BD...")
        server = Server.objects.create(
            name='Cobblemon Server (Real)',
            host=SERVER_HOST,
            container_name=SERVER_CONTAINER,
            rcon_port=RCON_PORT,
            rcon_password=RCON_PASSWORD,
            minecraft_data_path='/data',
            is_active=True,
            enable_whitelist=True,
            online_mode=False,
            auth_mode='whitelist',
            server_type='fabric',
            minecraft_version='1.21.1'
        )
        print(f"✅ Servidor creado con ID: {server.id}")
    else:
        # Actualizar configuración si es necesario
        print(f"\n✅ Servidor encontrado: {server.name} (ID: {server.id})")
        if server.rcon_password != RCON_PASSWORD:
            print(f"   Actualizando RCON password...")
            server.rcon_password = RCON_PASSWORD
            server.save()
        if server.host != SERVER_HOST:
            print(f"   Actualizando host...")
            server.host = SERVER_HOST
            server.save()
        if server.container_name != SERVER_CONTAINER:
            print(f"   Actualizando container_name...")
            server.container_name = SERVER_CONTAINER
            server.save()
    
    # Asegurar que el usuario tiene acceso
    UserServerRole.objects.get_or_create(
        user=admin_user,
        server=server,
        defaults={'role': 'admin'}
    )
    
    # Autenticar
    login_success = client.login(username='test_admin_real_whitelist', password='test_password_123')
    if not login_success:
        print("❌ Error: No se pudo autenticar")
        return False
    print("✅ Autenticación exitosa")
    
    # Test 1: Verificar que podemos obtener la whitelist actual
    print("\n🧪 Test 1: Obtener whitelist actual")
    response = client.get(f'/api/servers/{server.id}/whitelist/')
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        response_data = json.loads(response.content)
        current_whitelist = response_data.get('data', [])
        print(f"✅ Whitelist actual: {len(current_whitelist)} usuario(s)")
        if current_whitelist:
            print(f"   Usuarios: {', '.join([u.get('name', '') for u in current_whitelist[:5]])}")
    else:
        print(f"⚠️  No se pudo obtener whitelist: {response.status_code}")
    
    # Test 2: Agregar usuario de prueba a whitelist
    print("\n🧪 Test 2: Agregar usuario a whitelist (REAL)")
    test_username = 'TestPlayerReal_' + str(int(os.urandom(2).hex(), 16))
    
    print(f"   Usuario de prueba: {test_username}")
    response = client.post(
        f'/api/servers/{server.id}/whitelist/add/',
        data=json.dumps({'username': test_username}),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    response_data = json.loads(response.content)
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if response.status_code == 200:
        if response_data.get('success'):
            print(f"✅ Usuario '{test_username}' agregado a whitelist correctamente!")
            print(f"   Mensaje: {response_data.get('message')}")
            print(f"   Respuesta RCON: {response_data.get('response', 'N/A')}")
            
            # Verificar que aparece en la whitelist
            print("\n🧪 Test 3: Verificar que el usuario aparece en la whitelist")
            response = client.get(f'/api/servers/{server.id}/whitelist/')
            
            if response.status_code == 200:
                response_data = json.loads(response.content)
                updated_whitelist = response_data.get('data', [])
                usernames = [u.get('name', '') for u in updated_whitelist]
                
                if test_username in usernames:
                    print(f"✅ Usuario '{test_username}' encontrado en la whitelist!")
                    print(f"   Total de usuarios: {len(updated_whitelist)}")
                else:
                    print(f"⚠️  Usuario '{test_username}' no encontrado en la whitelist")
                    print(f"   Usuarios actuales: {', '.join(usernames[:10])}")
            
            # Limpiar: remover el usuario de prueba
            print("\n🧹 Limpiando: Removiendo usuario de prueba...")
            response = client.post(
                f'/api/servers/{server.id}/whitelist/remove/',
                data=json.dumps({'username': test_username}),
                content_type='application/json'
            )
            
            if response.status_code == 200 and response_data.get('success'):
                print(f"✅ Usuario de prueba removido correctamente")
            else:
                print(f"⚠️  No se pudo remover el usuario de prueba (puede que no exista)")
            
            return True
        else:
            print(f"❌ Error: {response_data.get('error')}")
            return False
    elif response.status_code == 500:
        error_msg = response_data.get('error', 'Unknown error')
        print(f"❌ Error 500: {error_msg}")
        print(f"   Esto puede indicar que:")
        print(f"   - RCON no está disponible")
        print(f"   - El servidor no está corriendo")
        print(f"   - La contraseña RCON es incorrecta")
        print(f"   - No se puede conectar al servidor")
        return False
    else:
        print(f"❌ Error inesperado: {response.status_code}")
        print(f"   Response: {json.dumps(response_data, indent=2)}")
        return False

if __name__ == '__main__':
    try:
        success = test_whitelist_add_real()
        print("\n" + "=" * 60)
        if success:
            print("✅ TEST EXITOSO - El endpoint funciona con servidor REAL")
        else:
            print("❌ TEST FALLIDO - Revisar configuración RCON")
        print("=" * 60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

