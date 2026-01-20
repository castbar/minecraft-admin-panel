#!/usr/bin/env python3
"""
Script para probar todos los endpoints del panel de administración de Minecraft
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
from django.contrib.auth import get_user_model
from server.models import Server, UserServerRole, MinecraftUser

User = get_user_model()

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"   {msg}")

# Datos para limpiar después
created_servers = []
created_users = []
created_minecraft_users = []

try:
    # Crear cliente de test
    client = Client()
    
    # Crear usuario admin para pruebas
    print_section("PREPARACIÓN")
    admin_user, created = User.objects.get_or_create(
        username='test_admin_endpoints',
        defaults={'is_staff': True, 'is_superuser': False, 'email': 'test@example.com'}
    )
    if created or not admin_user.check_password('test_password_123'):
        admin_user.set_password('test_password_123')
        admin_user.save()
        print_success(f"Usuario de test creado/actualizado: {admin_user.username}")
    else:
        print_success(f"Usuario de test existente: {admin_user.username}")
    
    # ========== AUTENTICACIÓN ==========
    print_section("1. AUTENTICACIÓN")
    
    # Login
    login_success = client.login(username='test_admin_endpoints', password='test_password_123')
    if login_success:
        print_success("Login exitoso")
    else:
        print_error("Login fallido")
        sys.exit(1)
    
    # Check Auth
    response = client.get('/api/auth/check/')
    if response.status_code == 200:
        data = json.loads(response.content)
        print_success(f"Check Auth: {data.get('authenticated')}")
        print_info(f"Usuario: {data.get('user', {}).get('username')}")
    else:
        print_error(f"Check Auth falló: {response.status_code}")
    
    # ========== SERVIDORES ==========
    print_section("2. GESTIÓN DE SERVIDORES")
    
    # Listar servidores
    response = client.get('/api/servers/')
    if response.status_code == 200:
        data = json.loads(response.content)
        servers = data.get('data', [])
        print_success(f"Listar servidores: {len(servers)} encontrados")
        test_server_id = None
        if servers:
            test_server_id = servers[0].get('id')
            print_info(f"Usando servidor existente: {servers[0].get('name')} (ID: {test_server_id})")
        else:
            # Crear servidor de prueba
            print_info("No hay servidores, creando uno de prueba...")
            server_data = {
                'name': 'Servidor de Prueba Endpoints',
                'host': 'test-server.local',
                'rcon_port': 25575,
                'rcon_password': 'test_rcon_password_123',
                'server_type': 'vanilla',
                'minecraft_version': '1.21.1'
            }
            response = client.post('/api/servers/create/', 
                                 json.dumps(server_data),
                                 content_type='application/json')
            if response.status_code in [200, 201]:
                data = json.loads(response.content)
                if data.get('success'):
                    test_server_id = data.get('data', {}).get('id')
                    created_servers.append(test_server_id)
                    print_success(f"Servidor creado: ID {test_server_id}")
                else:
                    print_error(f"Error creando servidor: {data.get('error')}")
            else:
                print_error(f"Error creando servidor: {response.status_code}")
    else:
        print_error(f"Listar servidores falló: {response.status_code}")
    
    if test_server_id:
        # Status del servidor
        response = client.get(f'/api/servers/{test_server_id}/status/')
        if response.status_code == 200:
            print_success("Status del servidor")
        else:
            print_warning(f"Status del servidor: {response.status_code}")
        
        # Stats del servidor
        response = client.get(f'/api/servers/{test_server_id}/stats/')
        if response.status_code == 200:
            print_success("Stats del servidor")
        else:
            print_warning(f"Stats del servidor: {response.status_code}")
        
        # Logs del servidor
        response = client.get(f'/api/servers/{test_server_id}/logs/?lines=50')
        if response.status_code == 200:
            print_success("Logs del servidor")
        else:
            print_warning(f"Logs del servidor: {response.status_code}")
        
        # Container info
        response = client.get(f'/api/servers/{test_server_id}/container/')
        if response.status_code == 200:
            print_success("Container info")
        else:
            print_warning(f"Container info: {response.status_code}")
        
        # Settings del servidor
        response = client.get(f'/api/servers/{test_server_id}/settings/')
        if response.status_code == 200:
            print_success("Settings del servidor")
        else:
            print_warning(f"Settings del servidor: {response.status_code}")
        
        # ========== WHITELIST ==========
        print_section("3. WHITELIST")
        
        # Listar whitelist
        response = client.get(f'/api/servers/{test_server_id}/whitelist/')
        if response.status_code == 200:
            data = json.loads(response.content)
            print_success(f"Listar whitelist: {len(data.get('data', []))} jugadores")
        else:
            print_warning(f"Listar whitelist: {response.status_code}")
        
        # Agregar a whitelist (solo si el servidor tiene RCON configurado)
        # response = client.post(f'/api/servers/{test_server_id}/whitelist/add/',
        #                       json.dumps({'username': 'TestPlayer123'}),
        #                       content_type='application/json')
        # if response.status_code == 200:
        #     print_success("Agregar a whitelist")
        # else:
        #     print_warning(f"Agregar a whitelist: {response.status_code}")
        
        # ========== USUARIOS MINECRAFT ==========
        print_section("4. USUARIOS MINECRAFT")
        
        # Listar usuarios Minecraft
        response = client.get(f'/api/servers/{test_server_id}/users/')
        if response.status_code == 200:
            data = json.loads(response.content)
            users = data.get('data', [])
            print_success(f"Listar usuarios Minecraft: {len(users)} encontrados")
        else:
            print_warning(f"Listar usuarios Minecraft: {response.status_code}")
        
        # ========== MODS ==========
        print_section("5. MODS")
        
        # Listar mods
        response = client.get(f'/api/servers/{test_server_id}/mods/')
        if response.status_code == 200:
            data = json.loads(response.content)
            mods = data.get('data', [])
            print_success(f"Listar mods: {len(mods)} encontrados")
        else:
            print_warning(f"Listar mods: {response.status_code}")
        
        # Pool de mods
        response = client.get('/api/mods/pool/')
        if response.status_code == 200:
            data = json.loads(response.content)
            pool_mods = data.get('data', [])
            print_success(f"Pool de mods: {len(pool_mods)} disponibles")
        else:
            print_warning(f"Pool de mods: {response.status_code}")
        
        # Categorías de mods
        response = client.get('/api/mods/pool/categories/')
        if response.status_code == 200:
            print_success("Categorías de mods")
        else:
            print_warning(f"Categorías de mods: {response.status_code}")
        
        # ========== BACKUPS ==========
        print_section("6. BACKUPS")
        
        # Listar backups
        response = client.get(f'/api/servers/{test_server_id}/backups/')
        if response.status_code == 200:
            data = json.loads(response.content)
            backups = data.get('data', [])
            print_success(f"Listar backups: {len(backups)} encontrados")
        else:
            print_warning(f"Listar backups: {response.status_code}")
        
        # Listar schedules de backups
        response = client.get(f'/api/servers/{test_server_id}/backup-schedules/')
        if response.status_code == 200:
            data = json.loads(response.content)
            schedules = data.get('data', [])
            print_success(f"Schedules de backups: {len(schedules)} encontrados")
        else:
            print_warning(f"Schedules de backups: {response.status_code}")
        
        # ========== VERSIONES MINECRAFT ==========
        print_section("7. VERSIONES MINECRAFT")
        
        # Listar versiones
        response = client.get('/api/minecraft/versions/')
        if response.status_code == 200:
            data = json.loads(response.content)
            versions = data.get('data', [])
            print_success(f"Versiones disponibles: {len(versions)}")
        else:
            print_warning(f"Versiones: {response.status_code}")
        
        # Última versión
        response = client.get('/api/minecraft/versions/latest/')
        if response.status_code == 200:
            data = json.loads(response.content)
            print_success(f"Última versión: {data.get('data', {}).get('version')}")
        else:
            print_warning(f"Última versión: {response.status_code}")
        
        # ========== USUARIOS DJANGO ==========
        print_section("8. USUARIOS DJANGO")
        
        # Listar usuarios
        response = client.get('/api/users/')
        if response.status_code == 200:
            data = json.loads(response.content)
            users = data.get('data', [])
            print_success(f"Usuarios Django: {len(users)} encontrados")
        else:
            print_warning(f"Usuarios Django: {response.status_code}")
        
        # Permisos del usuario actual
        response = client.get('/api/users/me/permissions/')
        if response.status_code == 200:
            print_success("Permisos del usuario actual")
        else:
            print_warning(f"Permisos: {response.status_code}")
        
        # ========== ROLES ==========
        if test_server_id:
            print_section("9. ROLES EN SERVIDOR")
            
            # Listar roles
            response = client.get(f'/api/servers/{test_server_id}/roles/')
            if response.status_code == 200:
                data = json.loads(response.content)
                roles = data.get('data', [])
                print_success(f"Roles en servidor: {len(roles)} encontrados")
            else:
                print_warning(f"Roles: {response.status_code}")
        
        # ========== SEGURIDAD ==========
        print_section("10. SEGURIDAD")
        
        # Security logs
        response = client.get('/api/security/logs/')
        if response.status_code == 200:
            data = json.loads(response.content)
            logs = data.get('data', [])
            print_success(f"Security logs: {len(logs)} encontrados")
        else:
            print_warning(f"Security logs: {response.status_code}")
        
        # ========== SESIONES ==========
        print_section("11. SESIONES")
        
        # Saved sessions
        response = client.get('/api/servers/sessions/')
        if response.status_code == 200:
            data = json.loads(response.content)
            sessions = data.get('data', [])
            print_success(f"Sesiones guardadas: {len(sessions)}")
        else:
            print_warning(f"Sesiones: {response.status_code}")
    
    # ========== LIMPIEZA ==========
    print_section("LIMPIEZA")
    
    # Eliminar servidores creados
    for server_id in created_servers:
        try:
            response = client.delete(f'/api/servers/{server_id}/delete/')
            if response.status_code in [200, 204]:
                print_success(f"Servidor {server_id} eliminado")
            else:
                print_warning(f"No se pudo eliminar servidor {server_id}: {response.status_code}")
        except Exception as e:
            print_warning(f"Error eliminando servidor {server_id}: {e}")
    
    # Eliminar usuarios Django creados
    for user_id in created_users:
        try:
            User.objects.filter(id=user_id).delete()
            print_success(f"Usuario Django {user_id} eliminado")
        except Exception as e:
            print_warning(f"Error eliminando usuario {user_id}: {e}")
    
    # Eliminar usuarios Minecraft creados
    for mc_user_id in created_minecraft_users:
        try:
            MinecraftUser.objects.filter(id=mc_user_id).delete()
            print_success(f"Usuario Minecraft {mc_user_id} eliminado")
        except Exception as e:
            print_warning(f"Error eliminando usuario Minecraft {mc_user_id}: {e}")
    
    print_section("RESUMEN")
    print_success("Pruebas completadas")
    
except Exception as e:
    print_error(f"Error durante las pruebas: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
