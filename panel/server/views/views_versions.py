"""
Vistas para gestionar versiones de Minecraft disponibles
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from ..models.models_versions import MinecraftVersion

@require_http_methods(["GET"])
def available_versions(request):
    """
    Obtener lista de versiones de Minecraft disponibles
    
    Query params:
        - server_type: (opcional) Filtrar por tipo de servidor (vanilla, fabric, forge, etc.)
        - stable_only: (opcional) Solo versiones estables (true/false)
    
    Response:
    {
        "success": true,
        "data": [
            {
                "version": "1.20.1",
                "display_name": "1.20.1 - Latest",
                "is_latest": true,
                "is_stable": true,
                "server_types": ["vanilla", "fabric", "forge", "paper"],
                "release_date": "2023-06-07"
            },
            ...
        ]
    }
    """
    try:
        server_type = request.GET.get('server_type')
        stable_only = request.GET.get('stable_only', 'false').lower() == 'true'
        
        # Obtener versiones disponibles
        versions = MinecraftVersion.get_available_versions(server_type)
        
        if stable_only:
            versions = versions.filter(is_stable=True)
        
        # Serializar versiones
        versions_data = []
        for version in versions:
            versions_data.append({
                'version': version.version,
                'display_name': version.display_name,
                'is_latest': version.is_latest,
                'is_stable': version.is_stable,
                'server_types': version.server_types,
                'release_date': version.release_date.isoformat() if version.release_date else None,
                'notes': version.notes,
            })
        
        return JsonResponse({
            'success': True,
            'data': versions_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def latest_version(request):
    """
    Obtener la versión más reciente de Minecraft
    
    Query params:
        - server_type: (opcional) Filtrar por tipo de servidor
    
    Response:
    {
        "success": true,
        "data": {
            "version": "1.20.1",
            "display_name": "1.20.1 - Latest",
            ...
        }
    }
    """
    try:
        server_type = request.GET.get('server_type')
        latest = MinecraftVersion.get_latest_version(server_type)
        
        if not latest:
            return JsonResponse({
                'success': False,
                'error': 'No version available'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'data': {
                'version': latest.version,
                'display_name': latest.display_name,
                'is_latest': latest.is_latest,
                'is_stable': latest.is_stable,
                'server_types': latest.server_types,
                'release_date': latest.release_date.isoformat() if latest.release_date else None,
                'notes': latest.notes,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_version(request):
    """
    Crear una nueva versión de Minecraft (solo staff)
    
    Body JSON:
    {
        "version": "1.20.2",
        "display_name": "1.20.2",
        "is_latest": false,
        "is_stable": true,
        "server_types": ["vanilla", "fabric", "paper"],
        "release_date": "2023-09-21",
        "notes": "Versión de corrección de errores"
    }
    """
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied: Only staff can create versions'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        if 'version' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Version is required'
            }, status=400)
        
        # Si se marca como latest, desmarcar las demás
        if data.get('is_latest', False):
            MinecraftVersion.objects.filter(is_latest=True).update(is_latest=False)
        
        # Crear versión
        version = MinecraftVersion.objects.create(
            version=data['version'],
            display_name=data.get('display_name', data['version']),
            is_latest=data.get('is_latest', False),
            is_stable=data.get('is_stable', True),
            server_types=data.get('server_types', []),
            release_date=data.get('release_date'),
            notes=data.get('notes', ''),
            is_supported=data.get('is_supported', True),
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Version {version.version} created',
            'data': {
                'id': version.id,
                'version': version.version,
                'display_name': version.display_name,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

