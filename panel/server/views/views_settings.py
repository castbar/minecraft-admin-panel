from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import os
import re
from ..models import Server, MinecraftUser
from ..utils.permissions import require_server_permission
# Importar función RCON desde views_api
try:
    from .views_api import _get_rcon_connection
except ImportError:
    # Fallback si no está disponible
    def _get_rcon_connection(server):
        import mcrcon
        try:
            rcon = mcrcon.MCRcon(server.host, server.rcon_password, port=server.rcon_port)
            rcon.connect()
            return rcon
        except:
            return None

@login_required
@require_server_permission('manage_settings')
@require_http_methods(["GET"])
def server_settings(request, server_id):
    """Obtener configuración del servidor"""
    server = request.server
    
    # Leer max-players y motd desde server.properties
    max_players = 20
    motd = "A Minecraft Server"
    server_properties_path = os.path.join(server.minecraft_data_path, 'server.properties')
    
    if os.path.exists(server_properties_path):
        with open(server_properties_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('max-players='):
                    try:
                        max_players = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith('motd='):
                    motd = line.split('=', 1)[1].replace('\\"', '"').replace('\\n', '\n')
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': server.id,
            'name': server.name,
            'host': server.host,
            'is_public': server.is_public,
            'auth_mode': server.auth_mode,
            'auth_mode_display': server.get_auth_mode_display_short(),
            'enable_whitelist': server.enable_whitelist,
            'api_key': server.api_key or None,  # No exponer si no existe
            'online_mode': server.online_mode,
            'is_active': server.is_active,
            'max_players': max_players,
            'motd': motd,
        }
    })

@csrf_exempt
@login_required
@require_server_permission('manage_settings')
@require_http_methods(["POST"])
def server_settings_update(request, server_id):
    """Actualizar configuración del servidor"""
    server = request.server
    data = json.loads(request.body)
    
    # Campos actualizables
    updatable_fields = ['is_public', 'auth_mode', 'enable_whitelist', 'online_mode', 'max_players', 'motd']
    
    for field in updatable_fields:
        if field in data:
            setattr(server, field, data[field])
    
    # Generar API key si se cambia a modo database/both y no existe
    if server.auth_mode in ['database', 'both'] and not server.api_key:
        server.generate_api_key()
    
    server.save()
    
    # Aplicar cambios al servidor Minecraft
    _apply_server_settings(server, data)
    
    return JsonResponse({
        'success': True,
        'message': 'Server settings updated',
        'data': {
            'is_public': server.is_public,
            'auth_mode': server.auth_mode,
            'enable_whitelist': server.enable_whitelist,
            'online_mode': server.online_mode,
            'max_players': getattr(server, 'max_players', None),
            'motd': getattr(server, 'motd', None),
        }
    })

def _apply_server_settings(server, data=None):
    """Aplicar configuración al servidor Minecraft vía RCON o archivos"""
    import os
    import re
    # Importar función RCON desde views_api
    try:
        from .views_api import _get_rcon_connection
    except ImportError:
        # Fallback si no está disponible
        import mcrcon
        def _get_rcon_connection(server):
            try:
                rcon = mcrcon.MCRcon(server.host, server.rcon_password, port=server.rcon_port)
                rcon.connect()
                return rcon
            except:
                return None
    
    # Modificar server.properties para cambios que requieren reinicio
    server_properties_path = os.path.join(server.minecraft_data_path, 'server.properties')
    
    if os.path.exists(server_properties_path):
        # Leer archivo
        with open(server_properties_path, 'r') as f:
            content = f.read()
        
        # Aplicar cambios según los datos recibidos
        if data:
            # Max players - modificar server.properties
            if 'max_players' in data:
                max_players = data['max_players']
                content = re.sub(r'^max-players=.*$', f'max-players={max_players}', content, flags=re.MULTILINE)
            
            # MOTD - modificar server.properties
            if 'motd' in data:
                motd = data['motd'].replace('\\', '\\\\').replace('"', '\\"')
                content = re.sub(r'^motd=.*$', f'motd={motd}', content, flags=re.MULTILINE)
            
            # Online mode - modificar server.properties
            if 'online_mode' in data:
                online_mode = 'true' if data['online_mode'] else 'false'
                content = re.sub(r'^online-mode=.*$', f'online-mode={online_mode}', content, flags=re.MULTILINE)
            
            # Whitelist - puede activarse/desactivarse vía RCON
            if 'enable_whitelist' in data:
                enable_whitelist = data['enable_whitelist']
                content = re.sub(r'^white-list=.*$', f'white-list={str(enable_whitelist).lower()}', content, flags=re.MULTILINE)
                
                # Intentar aplicar vía RCON si el servidor está online
                rcon = _get_rcon_connection(server)
                if rcon:
                    try:
                        if enable_whitelist:
                            rcon.command('whitelist on')
                        else:
                            rcon.command('whitelist off')
                    except:
                        pass
                    finally:
                        try:
                            rcon.disconnect()
                        except:
                            pass
        
        # Escribir archivo modificado
        with open(server_properties_path, 'w') as f:
            f.write(content)
        
        print(f"✅ server.properties actualizado para {server.name}")
    
    # Log de cambios
    print(f"Aplicando settings para servidor {server.name}:")
    print(f"  - is_public: {server.is_public}")
    print(f"  - auth_mode: {server.auth_mode}")
    print(f"  - enable_whitelist: {server.enable_whitelist}")
    print(f"  - online_mode: {server.online_mode}")
    if data:
        if 'max_players' in data:
            print(f"  - max_players: {data['max_players']}")
        if 'motd' in data:
            print(f"  - motd: {data['motd']}")

@login_required
@require_server_permission('manage_users')
@require_http_methods(["GET"])
def minecraft_users_list(request, server_id):
    """Listar usuarios de Minecraft en base de datos"""
    server = request.server
    
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': False,
            'error': 'Server does not use database authentication'
        }, status=400)
    
    users = MinecraftUser.objects.filter(server=server).values(
        'id', 'username', 'is_active', 'last_login', 'created_at'
    )
    
    return JsonResponse({
        'success': True,
        'data': list(users)
    })

def _send_password_set_email(user, token):
    """Enviar email con token para establecer contraseña"""
    from django.core.mail import send_mail
    from django.conf import settings
    from django.template.loader import render_to_string
    
    try:
        # Construir URL para establecer contraseña
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        set_password_url = f"{site_url}/api/servers/{user.server.id}/users/set-password/?token={token}"
        
        # Renderizar template de email
        context = {
            'username': user.username,
            'server_name': user.server.name,
            'set_password_url': set_password_url,
            'token': token,
            'expires_hours': 24,
        }
        
        subject = f'Establece tu contraseña - {user.server.name}'
        message = render_to_string('emails/password_set_invitation.txt', context)
        html_message = render_to_string('emails/password_set_invitation.html', context) if os.path.exists(os.path.join(settings.BASE_DIR, 'templates', 'emails', 'password_set_invitation.html')) else None
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        import traceback
        traceback.print_exc()
        return False

@csrf_exempt
@login_required
@require_server_permission('manage_users')
@require_http_methods(["POST"])
def minecraft_user_create(request, server_id):
    """Crear usuario de Minecraft - Admin crea usuario y se envía email para establecer contraseña"""
    server = request.server
    
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': False,
            'error': 'Server does not use database authentication'
        }, status=400)
    
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')  # Opcional, para casos especiales
    
    if not username or len(username) < 3:
        return JsonResponse({
            'success': False,
            'error': 'Username must be at least 3 characters'
        }, status=400)
    
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email is required'
        }, status=400)
    
    # Validar formato de email básico
    if '@' not in email or '.' not in email.split('@')[1]:
        return JsonResponse({
            'success': False,
            'error': 'Invalid email format'
        }, status=400)
    
    if MinecraftUser.objects.filter(server=server, username=username).exists():
        return JsonResponse({
            'success': False,
            'error': 'Username already exists'
        }, status=400)
    
    # Crear usuario (sin contraseña inicialmente)
    user = MinecraftUser(server=server, username=username, email=email, is_active=False)
    
    # Si se proporciona password (caso especial), establecerlo directamente
    if password:
        if len(password) < 6:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }, status=400)
        user.set_password(password)
        user.is_active = True
    else:
        # Generar token para establecer contraseña
        token = user.generate_password_set_token()
        
        # Enviar email con token
        email_sent = _send_password_set_email(user, token)
        if not email_sent:
            return JsonResponse({
                'success': False,
                'error': 'Failed to send email. Please check email configuration.'
            }, status=500)
    
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': f'User {username} created. Email sent to {email}' if not password else f'User {username} created',
        'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'has_password_set': user.has_password_set(),
        }
    })

@csrf_exempt
@login_required
@require_server_permission('manage_users')
@require_http_methods(["POST"])
def minecraft_user_update(request, server_id, user_id):
    """Actualizar usuario de Minecraft"""
    server = request.server
    
    try:
        user = MinecraftUser.objects.get(id=user_id, server=server)
    except MinecraftUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    
    data = json.loads(request.body)
    
    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }, status=400)
        user.set_password(data['password'])
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': f'User {user.username} updated',
        'data': {
            'id': user.id,
            'username': user.username,
            'is_active': user.is_active,
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def minecraft_user_set_password(request, server_id):
    """Endpoint público para establecer contraseña usando token (sin autenticación requerida)"""
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    
    try:
        server = Server.objects.get(id=server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Server not found'
        }, status=404)
    
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': False,
            'error': 'Server does not use database authentication'
        }, status=400)
    
    data = json.loads(request.body)
    token = data.get('token', '').strip()
    password = data.get('password', '')
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Token is required'
        }, status=400)
    
    if not password:
        return JsonResponse({
            'success': False,
            'error': 'Password is required'
        }, status=400)
    
    if len(password) < 6:
        return JsonResponse({
            'success': False,
            'error': 'Password must be at least 6 characters'
        }, status=400)
    
    # Buscar usuario por token
    try:
        user = MinecraftUser.objects.get(
            server=server,
            password_set_token=token,
            password_set_token_expires__gt=timezone.now()
        )
    except MinecraftUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invalid or expired token'
        }, status=400)
    
    # Verificar que el token es válido
    if not user.is_password_set_token_valid(token):
        return JsonResponse({
            'success': False,
            'error': 'Invalid or expired token'
        }, status=400)
    
    # Establecer contraseña
    user.set_password(password)
    user.is_active = True
    user.password_set_token = None
    user.password_set_token_expires = None
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Password set successfully. Your account is now active.',
        'data': {
            'id': user.id,
            'username': user.username,
            'is_active': user.is_active,
        }
    })

@login_required
@require_server_permission('manage_users')
@require_http_methods(["DELETE"])
def minecraft_user_delete(request, server_id, user_id):
    """Eliminar usuario de Minecraft"""
    server = request.server
    
    try:
        user = MinecraftUser.objects.get(id=user_id, server=server)
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} deleted'
        })
    except MinecraftUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)

