"""
Vistas simplificadas para configurar mods desde la gestión de mods
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
import os
from ..models import Server, UserServerRole
from ..models.models_mods_pool import ModPool
from ..utils.permissions import _get_server_id_from_request

@login_required
@require_http_methods(["GET"])
def mod_config_get(request, server_id=None):
    """
    Obtener configuración de un mod - Requiere header X-Server-ID
    
    Query params:
    - mod_name: nombre del archivo del mod (ej: 'cobblemon.jar')
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
    
    mod_name = request.GET.get('mod_name', '').strip()
    if not mod_name:
        return JsonResponse({'success': False, 'error': 'mod_name parameter required'}, status=400)
    
    # Limpiar nombre (remover .jar, .disabled, etc.)
    clean_name = mod_name.replace('.jar', '').replace('.disabled', '').strip()
    
    # Buscar en pool de mods
    mod_pool = ModPool.objects.filter(name__iexact=clean_name).first()
    
    if not mod_pool or not mod_pool.config_file_path:
        return JsonResponse({
            'success': False,
            'error': 'Mod not found in pool or has no configuration'
        }, status=404)
    
    # Construir ruta del archivo de configuración
    config_file_path = os.path.join(server.minecraft_data_path, mod_pool.config_file_path)
    
    # Leer configuración actual si existe
    config_content = mod_pool.default_config
    file_exists = False
    
    if os.path.exists(config_file_path):
        file_exists = True
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error reading config file: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': True,
        'data': {
            'mod_name': mod_name,
            'mod_pool': {
                'id': mod_pool.id,
                'display_name': mod_pool.display_name,
                'mod_type': mod_pool.mod_type,
            },
            'config_file_path': mod_pool.config_file_path,
            'config_format': mod_pool.config_format,
            'config_content': config_content,
            'file_exists': file_exists,
            'is_default': config_content == mod_pool.default_config,
        }
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_config_update(request, server_id=None):
    """
    Actualizar configuración de un mod - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_name": "cobblemon.jar",
        "config_content": "{...}"
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
        mod_name = data.get('mod_name', '').strip()
        config_content = data.get('config_content', '').strip()
        
        if not mod_name:
            return JsonResponse({'success': False, 'error': 'mod_name is required'}, status=400)
        
        if not config_content:
            return JsonResponse({'success': False, 'error': 'config_content is required'}, status=400)
        
        # Limpiar nombre
        clean_name = mod_name.replace('.jar', '').replace('.disabled', '').strip()
        
        # Buscar en pool de mods
        mod_pool = ModPool.objects.filter(name__iexact=clean_name).first()
        
        if not mod_pool or not mod_pool.config_file_path:
            return JsonResponse({
                'success': False,
                'error': 'Mod not found in pool or has no configuration'
            }, status=404)
        
        # Validar formato JSON si es JSON
        if mod_pool.config_format == 'json':
            try:
                json.loads(config_content)
            except json.JSONDecodeError as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid JSON: {str(e)}'
                }, status=400)
        
        # Construir ruta del archivo
        config_file_path = os.path.join(server.minecraft_data_path, mod_pool.config_file_path)
        
        # Crear directorio si no existe
        config_dir = os.path.dirname(config_file_path)
        os.makedirs(config_dir, exist_ok=True)
        
        # Escribir archivo
        with open(config_file_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return JsonResponse({
            'success': True,
            'message': f'Configuration for {mod_pool.display_name} updated',
            'data': {
                'mod_name': mod_name,
                'config_file_path': mod_pool.config_file_path,
                'file_exists': True,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_config_reset(request, server_id=None):
    """
    Resetear configuración de un mod a los valores por defecto - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_name": "cobblemon.jar"
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
        mod_name = data.get('mod_name', '').strip()
        
        if not mod_name:
            return JsonResponse({'success': False, 'error': 'mod_name is required'}, status=400)
        
        # Limpiar nombre
        clean_name = mod_name.replace('.jar', '').replace('.disabled', '').strip()
        
        # Buscar en pool de mods
        mod_pool = ModPool.objects.filter(name__iexact=clean_name).first()
        
        if not mod_pool or not mod_pool.config_file_path or not mod_pool.default_config:
            return JsonResponse({
                'success': False,
                'error': 'Mod not found in pool or has no default configuration'
            }, status=404)
        
        # Construir ruta del archivo
        config_file_path = os.path.join(server.minecraft_data_path, mod_pool.config_file_path)
        
        # Crear directorio si no existe
        config_dir = os.path.dirname(config_file_path)
        os.makedirs(config_dir, exist_ok=True)
        
        # Escribir configuración por defecto
        with open(config_file_path, 'w', encoding='utf-8') as f:
            f.write(mod_pool.default_config)
        
        return JsonResponse({
            'success': True,
            'message': f'Configuration for {mod_pool.display_name} reset to default',
            'data': {
                'mod_name': mod_name,
                'config_file_path': mod_pool.config_file_path,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

