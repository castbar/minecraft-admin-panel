"""
Vistas para gestionar el pool de mods precargados
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
from ..models.models_mods_pool import ModPool

@login_required
@require_http_methods(["GET"])
def mods_pool_list(request):
    """
    Listar mods/plugins del pool disponibles
    Filtra por tipo de servidor si se proporciona server_id
    """
    server_type = request.GET.get('server_type')
    category = request.GET.get('category')
    is_popular = request.GET.get('is_popular', '').lower() == 'true'
    is_recommended = request.GET.get('is_recommended', '').lower() == 'true'
    
    mods = ModPool.objects.filter(is_active=True)
    
    # Filtrar por tipo de servidor
    if server_type:
        if server_type == 'vanilla':
            mods = mods.filter(compatible_vanilla=True)
        elif server_type == 'fabric':
            mods = mods.filter(compatible_fabric=True)
        elif server_type == 'forge':
            mods = mods.filter(compatible_forge=True)
        elif server_type == 'bukkit':
            mods = mods.filter(compatible_bukkit=True)
        elif server_type == 'spigot':
            mods = mods.filter(compatible_spigot=True)
        elif server_type == 'paper':
            mods = mods.filter(compatible_paper=True)
    
    # Filtrar por categoría
    if category:
        mods = mods.filter(category=category)
    
    # Filtrar populares
    if is_popular:
        mods = mods.filter(is_popular=True)
    
    # Filtrar recomendados
    if is_recommended:
        mods = mods.filter(is_recommended=True)
    
    mods = mods.order_by('-is_recommended', '-is_popular', 'display_name')
    
    data = [{
        'id': m.id,
        'name': m.name,
        'display_name': m.display_name,
        'mod_type': m.mod_type,
        'compatible_server_types': m.get_compatible_server_types(),
        'description': m.description,
        'category': m.category,
        'version': m.version,
        'is_popular': m.is_popular,
        'is_recommended': m.is_recommended,
        'has_config': bool(m.config_file_path),
        'config_file_path': m.config_file_path,
        'config_format': m.config_format,
        'modrinth_id': m.modrinth_id,
        'curseforge_id': m.curseforge_id,
        'download_url': m.download_url,
    } for m in mods]
    
    return JsonResponse({'success': True, 'data': data})

@login_required
@require_http_methods(["GET"])
def mods_pool_detail(request, mod_id):
    """
    Obtener detalles de un mod/plugin del pool
    Incluye configuración por defecto si existe
    """
    mod = get_object_or_404(ModPool, id=mod_id, is_active=True)
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': mod.id,
            'name': mod.name,
            'display_name': mod.display_name,
            'mod_type': mod.mod_type,
            'compatible_server_types': mod.get_compatible_server_types(),
            'description': mod.description,
            'category': mod.category,
            'version': mod.version,
            'is_popular': mod.is_popular,
            'is_recommended': mod.is_recommended,
            'config_file_path': mod.config_file_path,
            'config_format': mod.config_format,
            'default_config': mod.default_config,
            'has_config': bool(mod.config_file_path),
            'modrinth_id': mod.modrinth_id,
            'curseforge_id': mod.curseforge_id,
            'download_url': mod.download_url,
        }
    })

@login_required
@require_http_methods(["GET"])
def mods_pool_categories(request):
    """
    Listar categorías disponibles en el pool
    """
    categories = ModPool.objects.filter(
        is_active=True
    ).exclude(
        category=''
    ).values_list('category', flat=True).distinct()
    
    return JsonResponse({
        'success': True,
        'data': sorted(list(categories))
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mods_pool_create(request):
    """
    Crear nuevo mod/plugin en el pool (requiere staff)
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied: Staff only'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        mod = ModPool.objects.create(
            name=data.get('name', '').strip(),
            display_name=data.get('display_name', '').strip(),
            mod_type=data.get('mod_type', 'mod'),
            compatible_vanilla=data.get('compatible_vanilla', False),
            compatible_fabric=data.get('compatible_fabric', False),
            compatible_forge=data.get('compatible_forge', False),
            compatible_bukkit=data.get('compatible_bukkit', False),
            compatible_spigot=data.get('compatible_spigot', False),
            compatible_paper=data.get('compatible_paper', False),
            description=data.get('description', ''),
            category=data.get('category', ''),
            version=data.get('version', ''),
            is_popular=data.get('is_popular', False),
            is_recommended=data.get('is_recommended', False),
            config_file_path=data.get('config_file_path', ''),
            config_format=data.get('config_format', 'json'),
            default_config=data.get('default_config', ''),
            modrinth_id=data.get('modrinth_id', ''),
            curseforge_id=data.get('curseforge_id', ''),
            download_url=data.get('download_url', ''),
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Mod {mod.display_name} added to pool',
            'data': {
                'id': mod.id,
                'name': mod.name,
                'display_name': mod.display_name,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

