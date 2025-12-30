from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import os
from ..models import Server, UserServerRole, SecurityLog, MinecraftUser
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
    """Login API para app móvil - host opcional si el usuario solo tiene un servidor"""
    client_ip = _get_client_ip(request)
    
    try:
        data = json.loads(request.body)
        host = data.get('host', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not all([username, password]):
            return JsonResponse({
                'success': False,
                'error': 'Username and password required'
            }, status=400)
        
        # Autenticar usuario Django
        user = authenticate(request, username=username, password=password)
        if not user:
            # Registrar intento de login fallido
            SecurityLog.objects.create(
                log_type='failed_login',
                ip_address=client_ip,
                details={'message': f'Failed API login attempt for username: {username}', 'username': username}
            )
            return JsonResponse({
                'success': False,
                'error': 'Invalid credentials'
            }, status=401)
        
        # Login exitoso
        login(request, user)
        
        # Obtener servidores del usuario (si es staff, puede no tener servidores asignados)
        user_roles = UserServerRole.objects.filter(
            user=user
        ).select_related('server').filter(server__is_active=True)
        
        # Si el usuario es staff, puede acceder sin servidores asignados
        if not user_roles.exists() and not user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'No servers available for this user'
            }, status=403)
        
        # Si se proporciona host, intentar encontrarlo
        server = None
        user_role = None
        
        if user_roles.exists():
            if host:
                # Buscar servidor por host exacto
                for role in user_roles:
                    if role.server.host == host or role.server.host == host.split(':')[0]:
                        server = role.server
                        user_role = role
                        break
                
                # Si no se encuentra por host exacto, usar el primer servidor del usuario
                if not server:
                    user_role = user_roles.first()
                    server = user_role.server
            else:
                # Si no se proporciona host, usar el primer servidor del usuario
                user_role = user_roles.first()
                server = user_role.server if user_role else None
            
            # Verificar si el servidor está oculto y el cliente no está en la misma red
            if server:
                is_local_network = _is_local_network(client_ip)
                
                if server.is_hidden and not is_local_network:
                    SecurityLog.objects.create(
                        log_type='unauthorized_access',
                        ip_address=client_ip,
                        details={'message': f'User {user.username} attempted to access hidden server {server.host} from external network', 'username': user.username, 'host': server.host}
                    )
                    return JsonResponse({
                        'success': False,
                        'error': 'Server is hidden and not accessible from your network'
                    }, status=403)
                
                # Guardar sesión del servidor
                from ..models.models_multi import ServerSession
                ServerSession.objects.update_or_create(
                    user=user,
                    server=server,
                    defaults={'last_accessed': timezone.now()}
                )
        
        # Registrar login exitoso
        SecurityLog.objects.create(
            log_type='successful_login',
            ip_address=client_ip,
            details={'message': f'Successful API login for user: {user.username}', 'username': user.username, 'success': True}
        )
        
        # Obtener todos los servidores del usuario para el frontend
        all_user_roles = UserServerRole.objects.filter(
            user=user
        ).select_related('server').filter(server__is_active=True)
        
        servers_list = []
        for role in all_user_roles:
            servers_list.append({
                'id': role.server.id,
                'name': role.server.name,
                'host': role.server.host,
                'role': role.role,
            })
        
        # Preparar respuesta con información del usuario
        response_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email or '',
                'is_staff': user.is_staff,
            },
            'token': 'session-based',  # Por ahora sesión, luego JWT
            'servers': servers_list  # Lista completa de servidores disponibles
        }
        
        # Si hay servidor seleccionado, agregarlo
        if server and user_role:
            response_data['server'] = {
                'id': server.id,
                'name': server.name,
                'host': server.host,
                'role': user_role.role,
            }
        
        return JsonResponse({
            'success': True,
            'data': response_data
        })
            
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

@csrf_exempt
@require_http_methods(["GET"])
def api_check_auth(request):
    """Verificar si el usuario está autenticado (verificar sesión del servidor)"""
    from django.contrib.auth.decorators import login_required
    from ..models import UserServerRole
    from ..models.models_multi import ServerSession
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'authenticated': False,
            'error': 'Not authenticated'
        }, status=401)
    
    # Obtener servidores disponibles para el usuario
    user_servers = UserServerRole.objects.filter(user=request.user).select_related('server')
    servers = []
    for user_role in user_servers:
        if user_role.server.is_active:
            # Obtener información de sesión guardada
            session = ServerSession.objects.filter(
                user=request.user,
                server=user_role.server
            ).first()
            
            servers.append({
                'id': user_role.server.id,
                'name': user_role.server.name,
                'host': user_role.server.host,
                'role': user_role.role,
                'is_hidden': user_role.server.is_hidden,
                'last_accessed': session.last_accessed.isoformat() if session else None,
                'is_favorite': session.is_favorite if session else False,
            })
    
    return JsonResponse({
        'success': True,
        'authenticated': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
        },
        'servers': servers
    })

@csrf_exempt
@require_http_methods(["POST"])
def minecraft_user_authenticate(request, server_id):
    """
    Endpoint para que el plugin/mod valide usuarios de Minecraft
    Usado por: PanelAuth plugin/mod
    
    POST /api/servers/{server_id}/auth/
    Headers:
        X-API-Key: {api_key} (opcional, pero recomendado)
    Body:
        {
            "username": "player123",
            "password": "password123"
        }
    
    Response:
        {
            "valid": true,
            "username": "player123",
            "source": "database" | "whitelist"
        }
    """
    try:
        server = Server.objects.get(id=server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'error': 'Server not found'
        }, status=404)
    
    # Verificar API key (opcional pero recomendado)
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if server.api_key and not server.verify_api_key(api_key):
        return JsonResponse({
            'valid': False,
            'error': 'Invalid API key'
        }, status=401)
    
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username:
        return JsonResponse({
            'valid': False,
            'error': 'Username required'
        }, status=400)
    
    # Validar según modo de autenticación
    if server.auth_mode in ['database', 'both']:
        # Validar contra base de datos
        user = MinecraftUser.authenticate(server, username, password)
        if user:
            return JsonResponse({
                'valid': True,
                'username': user.username,
                'is_active': user.is_active,
                'source': 'database'
            })
    
    if server.auth_mode in ['whitelist', 'both']:
        # Validar contra whitelist
        if _is_in_whitelist(server, username):
            return JsonResponse({
                'valid': True,
                'username': username,
                'source': 'whitelist'
            })
    
    # Si llegamos aquí, las credenciales no son válidas
    return JsonResponse({
        'valid': False,
        'error': 'Invalid credentials'
    }, status=401)

def _is_in_whitelist(server, username):
    """Verificar si un usuario está en la whitelist"""
    try:
        # Intentar obtener whitelist vía RCON primero
        from mcrcon import MCRcon
        rcon = MCRcon(server.host, server.rcon_password, port=server.rcon_port)
        rcon.connect()
        response = rcon.command('whitelist list')
        rcon.disconnect()
        
        # Parsear respuesta: "There are X whitelisted players: player1, player2"
        if username.lower() in response.lower():
            return True
    except Exception as e:
        # Si falla RCON, intentar leer archivo
        pass
    
    # Fallback: leer archivo whitelist.json
    whitelist_path = os.path.join(server.minecraft_data_path, 'whitelist.json')
    if os.path.exists(whitelist_path):
        try:
            import json as json_lib
            with open(whitelist_path, 'r') as f:
                whitelist = json_lib.load(f)
            
            if isinstance(whitelist, list):
                for entry in whitelist:
                    if isinstance(entry, dict) and entry.get('name', '').lower() == username.lower():
                        return True
                    elif isinstance(entry, str) and entry.lower() == username.lower():
                        return True
        except Exception:
            pass
    
    return False
