from functools import wraps
from django.http import JsonResponse
from ..models import Server, UserServerRole

def require_server_permission(permission):
    """Decorador para verificar permisos en servidores"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            server_id = kwargs.get('server_id') or request.GET.get('server_id') or request.POST.get('server_id')
            
            if not server_id:
                return JsonResponse({'success': False, 'error': 'Server ID required'}, status=400)
            
            try:
                server = Server.objects.get(id=server_id)
                user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
                
                if not user_role:
                    return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
                
                if not user_role.has_permission(permission):
                    return JsonResponse({'success': False, 'error': f'Permission denied: {permission} required'}, status=403)
                
                # Agregar server y user_role al request para uso en la vista
                request.server = server
                request.user_role = user_role
                
                return view_func(request, *args, **kwargs)
            except Server.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        return wrapper
    return decorator

