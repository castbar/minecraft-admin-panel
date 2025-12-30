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
    """Crear nuevo usuario Django (solo staff)"""
    error = _check_staff_permission(request)
    if error:
        return error
    
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
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
        
        user = User.objects.create_user(
            username=username,
            email=email if email else '',
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
    """Cambiar contraseña de usuario (solo staff)"""
    error = _check_staff_permission(request)
    if error:
        return error
    
    try:
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body)
        new_password = data.get('new_password', '').strip()
        
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
        
        user.set_password(new_password)
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

