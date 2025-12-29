"""
Vistas para crear y gestionar contenedores Docker desde Django
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
import json
from .models import Server, UserServerRole
from .docker_control import (
    create_container_from_compose,
    get_container_status,
    get_container_info
)
from .notifications import send_notification

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
        
        # Crear registro en la base de datos (sin crear contenedor Docker)
        server = Server.objects.create(
            name=data['name'],
            host=data['host'],
            container_name=data.get('container_name', data['host']),
            rcon_port=data['rcon_port'],
            rcon_password=data['rcon_password'],
            minecraft_data_path=data.get('minecraft_data_path', '/data'),
            is_active=True,
            enable_whitelist=data.get('enable_whitelist', True),
            online_mode=data.get('online_mode', False),
            auth_mode=data.get('auth_mode', 'whitelist'),
        )
        
        # Asignar rol de admin al usuario que creó el servidor
        UserServerRole.objects.create(
            user=request.user,
            server=server,
            role='admin'
        )
        
        send_notification(server, 'server_created', f"Servidor '{server.name}' creado correctamente")
        
        return JsonResponse({
            'success': True,
            'message': f'Servidor {server.name} creado correctamente',
            'server_id': server.id,
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

