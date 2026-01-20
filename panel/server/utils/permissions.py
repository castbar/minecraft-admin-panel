from functools import wraps
from django.http import JsonResponse
import json
from ..models import Server, UserServerRole

def check_server_ownership(request, server):
    """Verificar que el usuario es propietario del servidor"""
    if server.owner != request.user:
        return False, JsonResponse({
            'success': False,
            'error': 'Permission denied: You are not the owner of this server'
        }, status=403)
    return True, None

def _get_server_id_from_request(request):
    """
    Helper común para obtener server_id de la request.
    TODOS los endpoints usan el mismo método.
    
    Orden de prioridad:
    1. Header HTTP: X-Server-ID (MÉTODO PRINCIPAL - todos los endpoints deben usarlo)
    2. URL parameter (path): /api/servers/<id>/... (compatibilidad)
    3. Query parameter: ?server_id=<id> (compatibilidad)
    4. Body JSON (POST): {"server_id": <id>} (compatibilidad)
    
    Returns: server_id (int) or None
    """
    # 1. Header HTTP (MÉTODO PRINCIPAL)
    server_id = request.headers.get('X-Server-ID')
    if server_id:
        try:
            return int(server_id)
        except (ValueError, TypeError):
            pass
    
    # 2. De la URL (compatibilidad - si está en el path, Django lo pone en kwargs)
    if hasattr(request, 'resolver_match') and request.resolver_match:
        server_id = request.resolver_match.kwargs.get('server_id')
        if server_id:
            return int(server_id)
    
    # 3. Query parameter (compatibilidad)
    server_id = request.GET.get('server_id')
    if server_id:
        try:
            return int(server_id)
        except (ValueError, TypeError):
            pass
    
    # 4. Body JSON (compatibilidad - solo para POST/PUT/PATCH)
    if request.method in ['POST', 'PUT', 'PATCH'] and request.body:
        try:
            data = json.loads(request.body)
            server_id = data.get('server_id')
            if server_id:
                return int(server_id)
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    
    return None

def require_server_permission(permission):
    """Decorador para verificar permisos en servidores - Solo el owner puede gestionar"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obtener server_id del header (método principal) o de otras fuentes (compatibilidad)
            server_id = _get_server_id_from_request(request) or kwargs.get('server_id')
            
            if not server_id:
                return JsonResponse({
                    'success': False, 
                    'error': 'Server ID required. Send header X-Server-ID: <id>'
                }, status=400)
            
            try:
                server = Server.objects.get(id=server_id, is_active=True)
                
                # Verificar que el usuario es el propietario del servidor
                if server.owner != request.user:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Permission denied: You are not the owner of this server'
                    }, status=403)
                
                # Agregar server al request para uso en la vista
                request.server = server
                
                return view_func(request, *args, **kwargs)
            except Server.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        return wrapper
    return decorator

