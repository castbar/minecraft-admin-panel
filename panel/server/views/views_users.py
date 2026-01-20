"""
Vistas para gestión de usuarios Django y roles en servidores
"""
import json
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from ..models import Server, UserServerRole
from ..utils.permissions import _get_server_id_from_request


def _check_staff_permission(request):
    """Verificar que el usuario es staff"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied: Staff access required'
        }, status=403)
    return None


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def django_users_list(request):
    """Listar todos los usuarios Django (solo staff)"""
    error = _check_staff_permission(request)
    if error:
        return error
    
    users = User.objects.all().order_by('username')
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email or '',
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    } for user in users]
    
    return JsonResponse({
        'success': True,
        'data': users_data
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def django_user_create(request):
    """Crear nuevo usuario Django (solo staff) - Envía email para establecer contraseña"""
    error = _check_staff_permission(request)
    if error:
        return error
    
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')  # Opcional - si no se proporciona, se envía email
        is_staff = data.get('is_staff', False)
        is_active = data.get('is_active', True)
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            }, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'error': 'Username already exists'
            }, status=400)
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email is required to send password setup link'
            }, status=400)
        
        # Validar formato de email
        if '@' not in email or '.' not in email.split('@')[1]:
            return JsonResponse({
                'success': False,
                'error': 'Invalid email format'
            }, status=400)
        
        # Si se proporciona password, crear usuario directamente
        if password:
            if len(password) < 6:
                return JsonResponse({
                    'success': False,
                    'error': 'Password must be at least 6 characters'
                }, status=400)
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=is_staff,
                is_active=is_active
            )
            
            return JsonResponse({
                'success': True,
                'message': f'User {user.username} created successfully',
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email or '',
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                }
            })
        else:
            # Crear usuario sin contraseña (inactivo) y enviar email
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            # Crear usuario inactivo (sin contraseña válida)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None,  # Sin contraseña inicial
                is_staff=is_staff,
                is_active=False  # Inactivo hasta que establezca contraseña
            )
            # Marcar que no tiene contraseña válida
            user.set_unusable_password()
            user.save()
            
            # Generar token para establecer contraseña
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Construir URL
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            set_password_url = f"{site_url}/api/users/set-password/?uid={uid}&token={token}"
            
            # Renderizar email
            context = {
                'username': user.username,
                'set_password_url': set_password_url,
                'token': token,
                'uid': uid,
                'expires_hours': 24,
            }
            
            subject = 'Establece tu contraseña - Minecraft Server Manager'
            message = f"""Hola {user.username},

Has sido invitado a crear una cuenta en Minecraft Server Manager.

Para establecer tu contraseña y activar tu cuenta, haz clic en el siguiente enlace:

{set_password_url}

Este enlace expirará en 24 horas.

Si no solicitaste esta cuenta, puedes ignorar este email.

Saludos,
Equipo de Minecraft Server Manager
"""
            
            # Enviar email
            email_sent = False
            try:
                # Usar EMAIL_FROM_NAME si está disponible
                from_email = settings.DEFAULT_FROM_EMAIL
                from_name = getattr(settings, 'EMAIL_FROM_NAME', 'Minecraft Server Manager')
                if from_name and from_email:
                    from_email = f"{from_name} <{from_email}>"
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception as e:
                print(f"Error enviando email: {e}")
                import traceback
                traceback.print_exc()
            
            if not email_sent:
                # Si falla el email, eliminar el usuario creado
                user.delete()
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to send email: {str(e)}'
                }, status=500)
            
            return JsonResponse({
                'success': True,
                'message': f'User {user.username} created. Email sent to {email}',
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email or '',
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                    'email_sent': True,
                }
            })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def django_user_detail(request, user_id):
    """Obtener detalles de un usuario Django (solo staff)"""
    error = _check_staff_permission(request)
    if error:
        return error
    
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Obtener roles del usuario
        roles = UserServerRole.objects.filter(user=user).select_related('server')
        roles_data = [{
            'id': role.id,
            'server': {
                'id': role.server.id,
                'name': role.server.name,
            },
            'role': role.role,
            'created_at': role.created_at.isoformat() if role.created_at else None,
        } for role in roles]
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email or '',
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'roles': roles_data,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT", "PATCH"])
def django_user_update(request, user_id):
    """Actualizar usuario Django (solo staff)"""
    error = _check_staff_permission(request)
    if error:
        return error
    
    try:
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body)
        
        # No permitir editar el superusuario desde aquí (seguridad)
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Cannot edit superuser'
            }, status=403)
        
        if 'email' in data:
            user.email = data['email'].strip()
        
        if 'is_staff' in data:
            # Solo superusers pueden cambiar is_staff
            if request.user.is_superuser:
                user.is_staff = data['is_staff']
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Only superusers can change is_staff'
                }, status=403)
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {user.username} updated successfully',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email or '',
                'is_staff': user.is_staff,
                'is_active': user.is_active,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def django_user_delete(request, user_id):
    """Eliminar usuario Django (solo staff)"""
    error = _check_staff_permission(request)
    if error:
        return error
    
    try:
        user = get_object_or_404(User, id=user_id)
        
        # No permitir eliminar el usuario actual
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete your own account'
            }, status=400)
        
        # No permitir eliminar superusers
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete superuser'
            }, status=403)
        
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def django_user_change_password(request, user_id):
    """Cambiar contraseña de usuario - Usuario puede cambiar su propia contraseña, staff puede cambiar cualquiera"""
    try:
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body)
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        # Verificar permisos: solo puede cambiar su propia contraseña o ser staff
        if user.id != request.user.id and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: You can only change your own password'
            }, status=403)
        
        if not new_password:
            return JsonResponse({
                'success': False,
                'error': 'new_password is required'
            }, status=400)
        
        if len(new_password) < 6:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }, status=400)
        
        # Si el usuario está cambiando su propia contraseña, verificar la actual
        if user.id == request.user.id:
            if not current_password:
                return JsonResponse({
                    'success': False,
                    'error': 'current_password is required to change your own password'
                }, status=400)
            
            if not user.check_password(current_password):
                return JsonResponse({
                    'success': False,
                    'error': 'Current password is incorrect'
                }, status=400)
        
        # Cambiar contraseña
        user.set_password(new_password)
        user.is_active = True  # Activar usuario si estaba inactivo
        user.save()
        
        # Si es el usuario actual, actualizar la sesión
        if user.id == request.user.id:
            update_session_auth_hash(request, user)
        
        return JsonResponse({
            'success': True,
            'message': f'Password changed successfully for {user.username}'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def server_roles_list(request, server_id):
    """Listar todos los roles asignados a un servidor"""
    try:
        server = get_object_or_404(Server, id=server_id, is_active=True)
        
        # Verificar que el usuario tiene acceso al servidor
        user_role = UserServerRole.objects.filter(
            user=request.user,
            server=server
        ).first()
        
        if not user_role:
            return JsonResponse({
                'success': False,
                'error': 'No access to this server'
            }, status=403)
        
        # Solo admins pueden ver la lista de roles
        if not user_role.has_permission('manage_users'):
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: manage_users required'
            }, status=403)
        
        roles = UserServerRole.objects.filter(server=server).select_related('user')
        roles_data = [{
            'id': role.id,
            'user': {
                'id': role.user.id,
                'username': role.user.username,
                'email': role.user.email or '',
            },
            'role': role.role,
            'created_at': role.created_at.isoformat() if role.created_at else None,
        } for role in roles]
        
        return JsonResponse({
            'success': True,
            'data': roles_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def server_role_assign(request, server_id):
    """Asignar rol a un usuario en un servidor (requiere permiso admin)"""
    try:
        server = get_object_or_404(Server, id=server_id, is_active=True)
        
        # Verificar que el usuario tiene permiso admin en el servidor
        user_role = UserServerRole.objects.filter(
            user=request.user,
            server=server
        ).first()
        
        if not user_role:
            return JsonResponse({
                'success': False,
                'error': 'No access to this server'
            }, status=403)
        
        if not user_role.has_permission('manage_users'):
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: manage_users required (admin role)'
            }, status=403)
        
        data = json.loads(request.body)
        user_id = data.get('user_id')
        role = data.get('role', '').strip().lower()
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'user_id is required'
            }, status=400)
        
        if role not in ['admin', 'moderator', 'viewer']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid role. Must be: admin, moderator, or viewer'
            }, status=400)
        
        try:
            user = get_object_or_404(User, id=user_id)
        except:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Crear o actualizar el rol
        role_obj, created = UserServerRole.objects.update_or_create(
            user=user,
            server=server,
            defaults={'role': role}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Role {role} assigned to {user.username}',
            'data': {
                'id': role_obj.id,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email or '',
                },
                'server': {
                    'id': server.id,
                    'name': server.name,
                },
                'role': role_obj.role,
                'created_at': role_obj.created_at.isoformat() if role_obj.created_at else None,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT", "PATCH"])
def server_role_update(request, server_id, role_id):
    """Actualizar rol de un usuario en un servidor (requiere permiso admin)"""
    try:
        server = get_object_or_404(Server, id=server_id, is_active=True)
        role_obj = get_object_or_404(UserServerRole, id=role_id, server=server)
        
        # Verificar que el usuario tiene permiso admin en el servidor
        user_role = UserServerRole.objects.filter(
            user=request.user,
            server=server
        ).first()
        
        if not user_role:
            return JsonResponse({
                'success': False,
                'error': 'No access to this server'
            }, status=403)
        
        if not user_role.has_permission('manage_users'):
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: manage_users required (admin role)'
            }, status=403)
        
        data = json.loads(request.body)
        new_role = data.get('role', '').strip().lower()
        
        if new_role not in ['admin', 'moderator', 'viewer']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid role. Must be: admin, moderator, or viewer'
            }, status=400)
        
        role_obj.role = new_role
        role_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Role updated to {new_role}',
            'data': {
                'id': role_obj.id,
                'user': {
                    'id': role_obj.user.id,
                    'username': role_obj.user.username,
                    'email': role_obj.user.email or '',
                },
                'server': {
                    'id': server.id,
                    'name': server.name,
                },
                'role': role_obj.role,
                'created_at': role_obj.created_at.isoformat() if role_obj.created_at else None,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def server_role_remove(request, server_id, role_id):
    """Remover rol de un usuario en un servidor (requiere permiso admin)"""
    try:
        server = get_object_or_404(Server, id=server_id, is_active=True)
        role_obj = get_object_or_404(UserServerRole, id=role_id, server=server)
        
        # Verificar que el usuario tiene permiso admin en el servidor
        user_role = UserServerRole.objects.filter(
            user=request.user,
            server=server
        ).first()
        
        if not user_role:
            return JsonResponse({
                'success': False,
                'error': 'No access to this server'
            }, status=403)
        
        if not user_role.has_permission('manage_users'):
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: manage_users required (admin role)'
            }, status=403)
        
        # No permitir remover el propio rol
        if role_obj.user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Cannot remove your own role'
            }, status=400)
        
        username = role_obj.user.username
        role_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Role removed from {username}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def user_roles_list(request, user_id):
    """Listar todos los servidores y roles de un usuario específico (solo staff o el mismo usuario)"""
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Solo staff o el mismo usuario puede ver sus roles
        if not request.user.is_staff and request.user.id != target_user.id:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        roles = UserServerRole.objects.filter(user=target_user).select_related('server')
        roles_data = [{
            'id': role.id,
            'server': {
                'id': role.server.id,
                'name': role.server.name,
                'host': role.server.host,
            },
            'role': role.role,
            'created_at': role.created_at.isoformat() if role.created_at else None,
        } for role in roles]
        
        return JsonResponse({
            'success': True,
            'data': {
                'user': {
                    'id': target_user.id,
                    'username': target_user.username,
                    'email': target_user.email or '',
                },
                'roles': roles_data
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def django_user_set_password(request):
    """Establecer contraseña usando token (sin autenticación requerida)"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from django.shortcuts import render
    from django.conf import settings
    
    # Obtener parámetros de URL (GET) o body (POST)
    if request.method == 'GET':
        uid = request.GET.get('uid', '').strip()
        token = request.GET.get('token', '').strip()
        
        if not uid or not token:
            return JsonResponse({
                'success': False,
                'error': 'uid and token are required in URL parameters'
            }, status=400)
        
        # Validar token y mostrar formulario
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(request, 'panel/set_password_error.html', {
                'error': 'Invalid token or user not found'
            }, status=400)
        
        # Verificar token
        if not default_token_generator.check_token(user, token):
            return render(request, 'panel/set_password_error.html', {
                'error': 'Invalid or expired token. Please request a new password reset link.'
            }, status=400)
        
        # Mostrar formulario HTML
        return render(request, 'panel/set_password.html', {
            'uid': uid,
            'token': token,
            'username': user.username,
            'site_url': getattr(settings, 'SITE_URL', 'http://100.77.240.103:8080'),
        })
    
    # POST: Procesar formulario
    try:
        # Intentar obtener de JSON primero (API)
        try:
            data = json.loads(request.body)
            uid = data.get('uid', '').strip()
            token = data.get('token', '').strip()
            password = data.get('password', '').strip()
        except json.JSONDecodeError:
            # Si no es JSON, obtener de form data (formulario HTML)
            uid = request.POST.get('uid', '').strip()
            token = request.POST.get('token', '').strip()
            password = request.POST.get('password', '').strip()
        
        if not uid or not token or not password:
            return JsonResponse({
                'success': False,
                'error': 'uid, token, and password are required'
            }, status=400)
        
        if len(password) < 6:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }, status=400)
        
        # Decodificar UID
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Invalid token or user not found'
            }, status=400)
        
        # Verificar token
        if not default_token_generator.check_token(user, token):
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired token'
            }, status=400)
        
        # Establecer contraseña y activar usuario
        user.set_password(password)
        user.is_active = True
        user.save()
        
        # Si es una petición de formulario HTML, mostrar página de éxito
        if request.content_type and 'application/json' not in request.content_type:
            return render(request, 'panel/set_password_success.html', {
                'username': user.username,
                'site_url': getattr(settings, 'SITE_URL', 'http://100.77.240.103:8080'),
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Password set successfully for {user.username}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["GET"])
def user_permissions(request):
    """Obtener permisos del usuario actual"""
    try:
        # Obtener todos los roles del usuario
        roles = UserServerRole.objects.filter(user=request.user).select_related('server')
        
        servers_data = []
        for role in roles:
            permissions = []
            if role.role == 'admin':
                permissions = ['view', 'manage_whitelist', 'manage_mods', 'control_server', 'view_logs', 'execute_commands', 'manage_users', 'manage_settings']
            elif role.role == 'moderator':
                permissions = ['view', 'manage_whitelist', 'view_logs', 'execute_commands']
            elif role.role == 'viewer':
                permissions = ['view', 'view_logs']
            
            servers_data.append({
                'server_id': role.server.id,
                'server_name': role.server.name,
                'role': role.role,
                'permissions': permissions,
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email or '',
                    'is_staff': request.user.is_staff,
                },
                'servers': servers_data
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

