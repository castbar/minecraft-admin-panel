"""
Vistas para páginas separadas del panel
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Server, UserServerRole
from .models_multi import ServerSession

def _get_user_server(request):
    """Obtener el servidor activo del usuario"""
    server_id = request.GET.get('server_id')
    if server_id:
        try:
            server = Server.objects.get(id=server_id, is_active=True)
            user_role = UserServerRole.objects.filter(
                user=request.user,
                server=server
            ).first()
            if user_role:
                ServerSession.objects.update_or_create(
                    user=request.user,
                    server=server,
                    defaults={'last_accessed': timezone.now()}
                )
                return server, user_role
        except Server.DoesNotExist:
            pass
    
    # Buscar en sesiones guardadas
    session = ServerSession.objects.filter(
        user=request.user
    ).select_related('server').order_by('-last_accessed').first()
    
    if session:
        user_role = UserServerRole.objects.filter(
            user=request.user,
            server=session.server
        ).first()
        if user_role:
            return session.server, user_role
    
    # Usar el primer servidor disponible
    user_role = UserServerRole.objects.filter(
        user=request.user
    ).select_related('server').filter(server__is_active=True).first()
    
    if user_role:
        return user_role.server, user_role
    
    return None, None

@login_required
def mods_page(request):
    """Página de mods"""
    server, user_role = _get_user_server(request)
    if not server:
        return redirect('/')
    
    context = {
        'server': server,
        'user_role': user_role,
    }
    return render(request, 'panel/mods.html', context)

@login_required
def players_page(request):
    """Página de jugadores"""
    server, user_role = _get_user_server(request)
    if not server:
        return redirect('/')
    
    context = {
        'server': server,
        'user_role': user_role,
    }
    return render(request, 'panel/players.html', context)

@login_required
def logs_page(request):
    """Página de logs"""
    server, user_role = _get_user_server(request)
    if not server:
        return redirect('/')
    
    context = {
        'server': server,
        'user_role': user_role,
    }
    return render(request, 'panel/logs.html', context)

@login_required
def control_page(request):
    """Página de control"""
    server, user_role = _get_user_server(request)
    if not server:
        return redirect('/')
    
    context = {
        'server': server,
        'user_role': user_role,
    }
    return render(request, 'panel/control.html', context)

@login_required
def settings_page(request):
    """Página de configuración del servidor"""
    server, user_role = _get_user_server(request)
    if not server:
        return redirect('/')
    
    # Verificar permisos
    if not user_role.has_permission('manage_settings'):
        return redirect('/')
    
    context = {
        'server': server,
        'user_role': user_role,
    }
    return render(request, 'panel/settings.html', context)
