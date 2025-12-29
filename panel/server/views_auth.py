from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Server, UserServerRole, SecurityLog
from django.utils import timezone

def _get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def _is_local_network(ip):
    """Verificar si la IP está en la red local/VPN"""
    import ipaddress
    
    local_ranges = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
        ipaddress.IPv4Network('100.0.0.0/8'),  # Tailscale
    ]
    
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        for network in local_ranges:
            if ip_obj in network:
                return True
    except:
        pass
    
    return False

# Vista de login personalizada que registra intentos
class LoggedLoginView(LoginView):
    """Vista de login que registra todos los intentos"""
    
    def form_valid(self, form):
        """Login exitoso"""
        client_ip = _get_client_ip(self.request)
        
        # Registrar login exitoso
        SecurityLog.objects.create(
            log_type='successful_login',
            ip_address=client_ip,
            details={'message': f'Successful login for user: {form.get_user().username}', 'username': form.get_user().username}
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Login fallido"""
        client_ip = _get_client_ip(self.request)
        username = form.data.get('username', 'unknown')
        
        # Registrar intento de login fallido
        SecurityLog.objects.create(
            log_type='failed_login',
            ip_address=client_ip,
            details={'message': f'Failed login attempt for username: {username}', 'username': username}
        )
        
        return super().form_invalid(form)

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """Login API para app móvil - requiere IP/host del servidor"""
    client_ip = _get_client_ip(request)
    
    try:
        data = json.loads(request.body)
        host = data.get('host', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not all([host, username, password]):
            return JsonResponse({
                'success': False,
                'error': 'Host, username and password required'
            }, status=400)
        
        # Autenticar usuario Django
        user = authenticate(request, username=username, password=password)
        if not user:
            # Registrar intento de login fallido
            SecurityLog.objects.create(
                log_type='failed_login',
                ip_address=client_ip,
                details={'message': f'Failed API login attempt for username: {username} (host: {host})', 'username': username, 'host': host}
            )
            return JsonResponse({
                'success': False,
                'error': 'Invalid credentials'
            }, status=401)
        
        # Verificar que el usuario tenga acceso al servidor
        try:
            server = Server.objects.get(host=host, is_active=True)
            user_role = UserServerRole.objects.filter(
                user=user,
                server=server
            ).first()
            
            if not user_role:
                SecurityLog.objects.create(
                    log_type='unauthorized_access',
                    ip_address=client_ip,
                    details={'message': f'User {user.username} attempted to access server {host} without permission', 'username': user.username, 'host': host}
                )
                return JsonResponse({
                    'success': False,
                    'error': 'No access to this server'
                }, status=403)
            
            # Verificar si el servidor está oculto y el cliente no está en la misma red
            is_local_network = _is_local_network(client_ip)
            
            if server.is_hidden and not is_local_network:
                SecurityLog.objects.create(
                    log_type='unauthorized_access',
                    ip_address=client_ip,
                    details={'message': f'User {user.username} attempted to access hidden server {host} from external network', 'username': user.username, 'host': host}
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Server is hidden and not accessible from your network'
                }, status=403)
            
            # Login exitoso
            login(request, user)
            
            # Registrar login exitoso
            SecurityLog.objects.create(
                log_type='successful_login',
                ip_address=client_ip,
                details={'message': f'Successful API login for user: {user.username} (host: {host})', 'username': user.username, 'host': host, 'success': True}
            )
            
            # Guardar sesión del servidor
            from .models_multi import ServerSession
            ServerSession.objects.update_or_create(
                user=user,
                server=server,
                defaults={'last_accessed': timezone.now()}
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'token': 'session-based',  # Por ahora sesión, luego JWT
                    'server': {
                        'id': server.id,
                        'name': server.name,
                        'host': server.host,
                        'role': user_role.role,
                    }
                }
            })
            
        except Server.DoesNotExist:
            SecurityLog.objects.create(
                log_type='unauthorized_access',
                ip_address=client_ip,
                details={'message': f'User {user.username} attempted to access non-existent server: {host}', 'username': user.username, 'host': host}
            )
            return JsonResponse({
                'success': False,
                'error': 'Server not found'
            }, status=404)
            
    except Exception as e:
        SecurityLog.objects.create(
            log_type='suspicious_activity',
            ip_address=client_ip,
            details={'message': f'Error during login attempt: {str(e)}', 'error': str(e)}
        )
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
