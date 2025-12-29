"""
Vistas para gestionar configuraciones de mods
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
from ..models import Server, UserServerRole
from ..models.models_mods import ModConfigTemplate, ServerModConfig
from ..utils.permissions import _get_server_id_from_request, require_server_permission

# ==================== PLANTILLAS GLOBALES ====================

@login_required
@require_http_methods(["GET"])
def mod_templates_list(request):
    """
    Listar todas las plantillas de configuración de mods disponibles
    No requiere server_id (es global)
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied: Staff only'}, status=403)
    
    templates = ModConfigTemplate.objects.filter(is_active=True).order_by('display_name')
    
    data = [{
        'id': t.id,
        'mod_name': t.mod_name,
        'display_name': t.display_name,
        'config_format': t.config_format,
        'config_file_path': t.config_file_path,
        'description': t.description,
        'has_default_config': bool(t.default_config),
    } for t in templates]
    
    return JsonResponse({'success': True, 'data': data})

@login_required
@require_http_methods(["GET"])
def mod_template_detail(request, template_id):
    """
    Obtener detalles de una plantilla de mod (incluye configuración por defecto)
    No requiere server_id (es global)
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied: Staff only'}, status=403)
    
    template = get_object_or_404(ModConfigTemplate, id=template_id, is_active=True)
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': template.id,
            'mod_name': template.mod_name,
            'display_name': template.display_name,
            'config_format': template.config_format,
            'config_file_path': template.config_file_path,
            'default_config': template.default_config,
            'description': template.description,
        }
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_template_create(request):
    """
    Crear una nueva plantilla de configuración de mod
    No requiere server_id (es global)
    Requiere staff
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied: Staff only'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        mod_name = data.get('mod_name', '').strip()
        display_name = data.get('display_name', '').strip()
        config_format = data.get('config_format', 'json')
        config_file_path = data.get('config_file_path', '').strip()
        default_config = data.get('default_config', '')
        description = data.get('description', '')
        
        if not mod_name:
            return JsonResponse({'success': False, 'error': 'mod_name is required'}, status=400)
        
        if not display_name:
            display_name = mod_name
        
        if not config_file_path:
            return JsonResponse({'success': False, 'error': 'config_file_path is required'}, status=400)
        
        # Validar formato JSON si es JSON
        if config_format == 'json' and default_config:
            try:
                json.loads(default_config)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON in default_config'}, status=400)
        
        template = ModConfigTemplate.objects.create(
            mod_name=mod_name,
            display_name=display_name,
            config_format=config_format,
            config_file_path=config_file_path,
            default_config=default_config,
            description=description,
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Template {display_name} created',
            'data': {
                'id': template.id,
                'mod_name': template.mod_name,
                'display_name': template.display_name,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_template_update(request, template_id):
    """
    Actualizar una plantilla de configuración de mod
    No requiere server_id (es global)
    Requiere staff
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied: Staff only'}, status=403)
    
    try:
        template = get_object_or_404(ModConfigTemplate, id=template_id)
        data = json.loads(request.body)
        
        if 'display_name' in data:
            template.display_name = data['display_name'].strip()
        
        if 'config_format' in data:
            template.config_format = data['config_format']
        
        if 'config_file_path' in data:
            template.config_file_path = data['config_file_path'].strip()
        
        if 'default_config' in data:
            default_config = data['default_config']
            # Validar formato JSON si es JSON
            if template.config_format == 'json' and default_config:
                try:
                    json.loads(default_config)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Invalid JSON in default_config'}, status=400)
            template.default_config = default_config
        
        if 'description' in data:
            template.description = data['description']
        
        if 'is_active' in data:
            template.is_active = data['is_active']
        
        template.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Template {template.display_name} updated',
            'data': {
                'id': template.id,
                'mod_name': template.mod_name,
                'display_name': template.display_name,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==================== CONFIGURACIONES POR SERVIDOR ====================

@login_required
@require_http_methods(["GET"])
def server_mod_configs_list(request, server_id=None):
    """
    Listar configuraciones de mods para un servidor - Requiere header X-Server-ID
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    # Verificar permisos
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    # Obtener configuraciones del servidor
    configs = ServerModConfig.objects.filter(server=server).select_related('mod_template')
    
    data = [{
        'id': c.id,
        'mod_template': {
            'id': c.mod_template.id,
            'mod_name': c.mod_template.mod_name,
            'display_name': c.mod_template.display_name,
            'config_format': c.mod_template.config_format,
            'config_file_path': c.mod_template.config_file_path,
        },
        'is_enabled': c.is_enabled,
        'has_custom_config': bool(c.config_content),
        'last_applied': c.last_applied.isoformat() if c.last_applied else None,
    } for c in configs]
    
    return JsonResponse({'success': True, 'data': data})

@login_required
@require_http_methods(["GET"])
def server_mod_config_detail(request, server_id=None, config_id=None):
    """
    Obtener detalles de una configuración de mod para un servidor - Requiere header X-Server-ID
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    # Verificar permisos
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    config = get_object_or_404(ServerModConfig, id=config_id, server=server)
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': config.id,
            'mod_template': {
                'id': config.mod_template.id,
                'mod_name': config.mod_template.mod_name,
                'display_name': config.mod_template.display_name,
                'config_format': config.mod_template.config_format,
                'config_file_path': config.mod_template.config_file_path,
            },
            'config_content': config.get_config_content(),
            'is_enabled': config.is_enabled,
            'last_applied': config.last_applied.isoformat() if config.last_applied else None,
        }
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def server_mod_config_create(request, server_id=None):
    """
    Crear/actualizar configuración de mod para un servidor - Requiere header X-Server-ID
    
    Body JSON:
    {
        "template_id": 1,
        "config_content": "{...}",  // Opcional, si no se envía usa la plantilla
        "is_enabled": true
    }
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    # Verificar permisos
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    try:
        data = json.loads(request.body)
        template_id = data.get('template_id')
        
        if not template_id:
            return JsonResponse({'success': False, 'error': 'template_id is required'}, status=400)
        
        template = get_object_or_404(ModConfigTemplate, id=template_id, is_active=True)
        
        config_content = data.get('config_content', '')
        is_enabled = data.get('is_enabled', True)
        
        # Validar formato JSON si es JSON
        if template.config_format == 'json' and config_content:
            try:
                json.loads(config_content)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON in config_content'}, status=400)
        
        # Crear o actualizar
        config, created = ServerModConfig.objects.update_or_create(
            server=server,
            mod_template=template,
            defaults={
                'config_content': config_content,
                'is_enabled': is_enabled,
                'created_by': request.user,
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Mod config {"created" if created else "updated"} for {template.display_name}',
            'data': {
                'id': config.id,
                'mod_template': {
                    'id': template.id,
                    'display_name': template.display_name,
                },
                'is_enabled': config.is_enabled,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def server_mod_config_apply(request, server_id=None, config_id=None):
    """
    Aplicar configuración de mod al servidor (escribir archivo) - Requiere header X-Server-ID
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    # Verificar permisos
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    config = get_object_or_404(ServerModConfig, id=config_id, server=server)
    
    if config.apply_to_server():
        return JsonResponse({
            'success': True,
            'message': f'Configuration for {config.mod_template.display_name} applied to server',
            'data': {
                'id': config.id,
                'last_applied': config.last_applied.isoformat() if config.last_applied else None,
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Failed to apply configuration (mod may be disabled)'
        }, status=400)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def server_mod_configs_apply_all(request, server_id=None):
    """
    Aplicar todas las configuraciones de mods habilitadas a un servidor - Requiere header X-Server-ID
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    # Verificar permisos
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    configs = ServerModConfig.objects.filter(server=server, is_enabled=True)
    
    applied = []
    failed = []
    
    for config in configs:
        if config.apply_to_server():
            applied.append(config.mod_template.display_name)
        else:
            failed.append(config.mod_template.display_name)
    
    return JsonResponse({
        'success': True,
        'message': f'Applied {len(applied)} configurations',
        'data': {
            'applied': applied,
            'failed': failed,
            'total': len(applied) + len(failed),
        }
    })

