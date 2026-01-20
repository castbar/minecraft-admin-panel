#!/usr/bin/env python3
"""
Script para crear un servidor real de pruebas y probar todos los endpoints
"""
import os
import sys
import django
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panel'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from server.models import Server, UserServerRole

User = get_user_model()

# Colores
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

client = Client()

# ========== PREPARACIÓN ==========
print_section("PREPARACIÓN")

# Crear usuario admin
admin_user, created = User.objects.get_or_create(
    username='test_admin_endpoints',
    defaults={'is_staff': True, 'is_superuser': False, 'email': 'test@example.com'}
)
if created or not admin_user.check_password('test_password_123'):
    admin_user.set_password('test_password_123')
    admin_user.save()
    print_success(f"Usuario creado/actualizado: {admin_user.username}")
else:
    print_success(f"Usuario existente: {admin_user.username}")

# Login
login_success = client.login(username='test_admin_endpoints', password='test_password_123')
if not login_success:
    print_error("Login fallido")
    sys.exit(1)
print_success("Login exitoso")

# ========== CREAR SERVIDOR ==========
print_section("CREAR SERVIDOR REAL DE PRUEBAS")

# Eliminar servidor de prueba anterior si existe
Server.objects.filter(name='Servidor Real de Pruebas').delete()
print_info("Servidores anteriores eliminados")

# Crear servidor en BD con el usuario como owner
server = Server.objects.create(
    name='Servidor Real de Pruebas',
    host='test-minecraft-server',
    container_name='test-minecraft-server',
    port=25565,
    rcon_port=25575,
    rcon_password='test_rcon_password_123',
    minecraft_data_path='/data',
    owner=admin_user,  # CRÍTICO: El usuario debe ser owner para evitar 403
    is_active=True,
    server_type='vanilla',
    minecraft_version='1.21.1',
    memory_limit_mb=1024,
    java_heap_max_mb=768,
    java_heap_min_mb=256
)
server_id = server.id
print_success(f"Servidor creado en BD: {server.name} (ID: {server_id})")
print_info(f"Owner: {server.owner.username}")

# Asignar rol admin también (por si acaso)
role, created = UserServerRole.objects.get_or_create(
    user=admin_user,
    server=server,
    defaults={'role': 'admin'}
)
if created:
    print_success("Rol admin asignado")
else:
    print_info(f"Rol existente: {role.role}")

# Intentar crear contenedor Docker (puede fallar si no hay acceso a Docker)
print_info("Intentando crear contenedor Docker...")
try:
    from server.views.views_docker import create_minecraft_container
    
    result = create_minecraft_container(
        container_name=server.container_name,
        server_type=server.server_type,
        minecraft_version=server.minecraft_version,
        rcon_port=server.rcon_port,
        rcon_password=server.get_rcon_password(),  # Obtener contraseña desencriptada
        memory_limit_mb=server.memory_limit_mb,
        java_heap_max_mb=server.java_heap_max_mb,
        java_heap_min_mb=server.java_heap_min_mb,
        minecraft_data_path=server.minecraft_data_path,
        minecraft_port=server.port,
        network='minecraft-servers',
        start_container=True,
        additional_ports=[]
    )
    
    if result.get('success'):
        print_success("Contenedor Docker creado")
    else:
        print_warning(f"Error creando contenedor: {result.get('error', 'Unknown')}")
except Exception as e:
    print_warning(f"Error al crear contenedor: {str(e)[:100]}")

# ========== PROBAR ENDPOINTS ==========
print_section("PROBAR ENDPOINTS DEL SERVIDOR")

server_endpoints = [
    (f'/api/servers/{server_id}/status/', 'Status'),
    (f'/api/servers/{server_id}/stats/', 'Stats'),
    (f'/api/servers/{server_id}/logs/?lines=10', 'Logs'),
    (f'/api/servers/{server_id}/container/', 'Container Info'),
    (f'/api/servers/{server_id}/settings/', 'Settings'),
    (f'/api/servers/{server_id}/whitelist/', 'Whitelist'),
    (f'/api/servers/{server_id}/users/', 'Minecraft Users'),
    (f'/api/servers/{server_id}/mods/', 'Mods'),
    (f'/api/servers/{server_id}/backups/', 'Backups'),
    (f'/api/servers/{server_id}/backup-schedules/', 'Backup Schedules'),
    (f'/api/servers/{server_id}/roles/', 'Roles'),
]

success_count = 0
error_count = 0

for url, name in server_endpoints:
    response = client.get(url)
    if response.status_code in [200, 201, 204]:
        print_success(f"{name}: {response.status_code}")
        success_count += 1
    else:
        error_msg = ""
        try:
            data = json.loads(response.content)
            err = data.get('error', '')
            if err:
                error_msg = f" - {err[:50]}"
        except:
            pass
        print_error(f"{name}: {response.status_code}{error_msg}")
        error_count += 1

# ========== ENDPOINTS GLOBALES ==========
print_section("ENDPOINTS GLOBALES")

global_endpoints = [
    ('/api/servers/', 'List Servers'),
    ('/api/mods/pool/', 'Mods Pool'),
    ('/api/mods/pool/categories/', 'Mods Categories'),
    ('/api/minecraft/versions/', 'Minecraft Versions'),
    ('/api/minecraft/versions/latest/', 'Latest Version'),
    ('/api/users/', 'Django Users'),
    ('/api/users/me/permissions/', 'My Permissions'),
    ('/api/security/logs/', 'Security Logs'),
    ('/api/servers/sessions/', 'Saved Sessions'),
    ('/api/auth/check/', 'Check Auth'),
]

for url, name in global_endpoints:
    response = client.get(url)
    if response.status_code in [200, 201, 204]:
        print_success(f"{name}: {response.status_code}")
        success_count += 1
    else:
        print_error(f"{name}: {response.status_code}")
        error_count += 1

# ========== LIMPIEZA ==========
print_section("LIMPIEZA")

# Eliminar servidor
try:
    # Intentar eliminar contenedor primero
    try:
        from server.views.views_docker import delete_container
        delete_result = delete_container(server.container_name, force=True)
        if delete_result.get('success'):
            print_success("Contenedor Docker eliminado")
    except:
        pass
    
    # Eliminar de BD
    Server.objects.filter(id=server_id).delete()
    print_success(f"Servidor {server_id} eliminado de BD")
except Exception as e:
    print_warning(f"Error en limpieza: {e}")

# ========== RESUMEN ==========
print_section("RESUMEN")
total = success_count + error_count
print_info(f"Endpoints exitosos: {success_count}/{total}")
print_info(f"Endpoints con error: {error_count}/{total}")

if error_count == 0:
    print_success("¡Todas las pruebas pasaron!")
else:
    print_warning(f"{error_count} endpoint(s) tuvieron problemas")
