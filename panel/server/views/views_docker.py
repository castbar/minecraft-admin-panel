"""
Vistas para crear y gestionar contenedores Docker desde Django
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
from ..models import Server, UserServerRole
from ..utils.docker_control import (
    create_container_from_compose,
    get_container_status,
    get_container_info
)
from ..utils.notifications import send_notification

def _check_server_permission(request, server_id, permission_needed):
    """Helper para verificar permisos"""
    server = get_object_or_404(Server, id=server_id, is_active=True)
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    
    if not user_role:
        return None, JsonResponse({
            'success': False, 
            'error': 'No access to this server'
        }, status=403)
    
    if not user_role.has_permission(permission_needed):
        return None, JsonResponse({
            'success': False, 
            'error': f'Permission denied: {permission_needed} required'
        }, status=403)
    
    return server, None

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_server(request):
    """
    Crear un nuevo servidor Minecraft (solo registro en BD, sin crear contenedor)
    
    Body JSON:
    {
        "name": "Nuevo Servidor",
        "host": "minecraft-server-2",
        "container_name": "minecraft-server-2",
        "rcon_port": 25575,
        "rcon_password": "password123",
        "minecraft_data_path": "/data"
    }
    """
    # Solo admins pueden crear servidores
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied: Only staff can create servers'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['name', 'host', 'rcon_port', 'rcon_password']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Validar puerto RCON
        rcon_port = int(data['rcon_port'])
        if rcon_port < 1 or rcon_port > 65535:
            return JsonResponse({
                'success': False,
                'error': 'Invalid RCON port: must be between 1 and 65535'
            }, status=400)
        
        # Crear registro en la base de datos (sin crear contenedor Docker)
        server = Server.objects.create(
            name=data['name'],
            host=data['host'],
            container_name=data.get('container_name', data['host']),
            rcon_port=rcon_port,
            rcon_password=data['rcon_password'],
            minecraft_data_path=data.get('minecraft_data_path', '/data'),
            is_active=True,
            enable_whitelist=data.get('enable_whitelist', True),
            online_mode=data.get('online_mode', False),
            auth_mode=data.get('auth_mode', 'whitelist'),
            is_public=data.get('is_public', False),
            is_hidden=data.get('is_hidden', False),
            # Tipo de servidor y versión
            server_type=data.get('server_type', 'vanilla'),
            minecraft_version=data.get('minecraft_version', 'latest'),
            # Mods y plugins base
            install_fabric_api=data.get('install_fabric_api', False),
            install_forge=data.get('install_forge', False),
            install_luckperms=data.get('install_luckperms', False),
            install_worldedit=data.get('install_worldedit', False),
            install_proximity_chat=data.get('install_proximity_chat', False),
            install_spark=data.get('install_spark', True),
            install_more_inventory=data.get('install_more_inventory', False),
            install_jei=data.get('install_jei', False),
            install_wthit=data.get('install_wthit', False),
            install_essentials=data.get('install_essentials', False),
            # Mods y plugins adicionales
            additional_mods=data.get('additional_mods', []),
            additional_plugins=data.get('additional_plugins', []),
        )
        
        # Asignar rol de admin al usuario que creó el servidor
        UserServerRole.objects.create(
            user=request.user,
            server=server,
            role='admin'
        )
        
        send_notification(server, 'server_created', f"Servidor '{server.name}' creado correctamente")
        
        # Retornar información completa del servidor creado (mantener server_id para compatibilidad)
        return JsonResponse({
            'success': True,
            'message': f'Servidor {server.name} creado correctamente',
            'server_id': server.id,  # Mantener para compatibilidad
            'data': {
                'id': server.id,
                'name': server.name,
                'host': server.host,
                'container_name': server.container_name,
                'rcon_port': server.rcon_port,
                'minecraft_data_path': server.minecraft_data_path,
                'is_active': server.is_active,
                'is_public': server.is_public,
                'is_hidden': server.is_hidden,
                'auth_mode': server.auth_mode,
                'enable_whitelist': server.enable_whitelist,
                'online_mode': server.online_mode,
                'server_type': server.server_type,
                'minecraft_version': server.minecraft_version,
                'role': 'admin',  # El usuario que crea el servidor siempre tiene rol admin
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def container_info(request, server_id):
    """Obtener información detallada del contenedor Docker"""
    server, error_response = _check_server_permission(request, server_id, 'view')
    if error_response:
        return error_response
    
    container_name = server.container_name or server.host
    info = get_container_info(container_name)
    
    if not info.get('success'):
        return JsonResponse({
            'success': False,
            'error': info.get('error', 'Contenedor no encontrado')
        }, status=404)
    
    return JsonResponse({
        'success': True,
        'data': info
    })

