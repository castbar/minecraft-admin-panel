"""
URL configuration for minecraft_panel project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.views.static import serve
from django.http import FileResponse, Http404
from pathlib import Path
import os
from server.views import views, views_api, views_settings, views_backup, views_auth, views_docker, views_pages, views_versions, views_mods, views_mods_config

# Ruta al frontend compilado (si existe)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'dist'

def serve_frontend_static(request, path):
    """Servir archivos estáticos del frontend con MIME types correctos"""
    file_path = FRONTEND_DIST / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(open(file_path, 'rb'), content_type=get_content_type(path))
    raise Http404()
    
def get_content_type(path):
    """Determinar el content type basado en la extensión del archivo"""
    ext = os.path.splitext(path)[1].lower()
    content_types = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
    }
    return content_types.get(ext, 'application/octet-stream')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints (deben ir antes del catch-all del frontend)
    path('api/', include([
        # API de autenticación
        path('auth/login/', views_auth.api_login, name='api_login'),
        path('servers/<int:server_id>/auth/', views_auth.minecraft_user_authenticate, name='minecraft_user_authenticate'),
        
        # API multi-servidor
        path('servers/switch/', views_api.switch_server, name='switch_server'),
        path('servers/sessions/', views_api.saved_sessions, name='saved_sessions'),
        path('security/logs/', views_api.security_logs, name='security_logs'),
        
        # API antigua (compatibilidad)
        path('whitelist/', views.whitelist_api, name='whitelist_api'),
        path('whitelist/<str:action>/', views.whitelist_action, name='whitelist_action'),
        path('mods/', views.mods_api, name='mods_api'),
        path('mods/<str:action>/', views.mods_action, name='mods_action'),
        path('players/', views.players_api, name='players_api'),
        path('logs/', views.logs_api, name='logs_api'),
        path('command/', views.command_api, name='command_api'),
        
        # API de mods (nueva estructura)
        path('servers/<int:server_id>/mods/', views_mods.mods_list, name='mods_list'),
        path('servers/<int:server_id>/mods/upload/', views_mods.mod_upload, name='mod_upload'),
        path('servers/<int:server_id>/mods/enable/', views_mods.mod_enable, name='mod_enable'),
        path('servers/<int:server_id>/mods/disable/', views_mods.mod_disable, name='mod_disable'),
        path('servers/<int:server_id>/mods/delete/', views_mods.mod_delete, name='mod_delete'),
        
        # API de configuraciones de mods (plantillas globales)
        path('mods/templates/', views_mods_config.mod_templates_list, name='mod_templates_list'),
        path('mods/templates/<int:template_id>/', views_mods_config.mod_template_detail, name='mod_template_detail'),
        path('mods/templates/create/', views_mods_config.mod_template_create, name='mod_template_create'),
        path('mods/templates/<int:template_id>/update/', views_mods_config.mod_template_update, name='mod_template_update'),
        
        # API de configuraciones de mods por servidor
        path('servers/<int:server_id>/mods/configs/', views_mods_config.server_mod_configs_list, name='server_mod_configs_list'),
        path('servers/<int:server_id>/mods/configs/create/', views_mods_config.server_mod_config_create, name='server_mod_config_create'),
        path('servers/<int:server_id>/mods/configs/<int:config_id>/', views_mods_config.server_mod_config_detail, name='server_mod_config_detail'),
        path('servers/<int:server_id>/mods/configs/<int:config_id>/apply/', views_mods_config.server_mod_config_apply, name='server_mod_config_apply'),
        path('servers/<int:server_id>/mods/configs/apply-all/', views_mods_config.server_mod_configs_apply_all, name='server_mod_configs_apply_all'),
        
        # API nueva (multi-servidor con roles)
        path('servers/', views_api.servers_list, name='servers_list'),
        path('servers/create/', views_docker.create_server, name='create_server'),
        path('servers/<int:server_id>/status/', views_api.server_status, name='server_status'),
        path('servers/<int:server_id>/stats/', views_api.server_stats, name='server_stats'),
        path('servers/<int:server_id>/control/<str:action>/', views_api.server_control, name='server_control'),
        path('servers/<int:server_id>/container/', views_docker.container_info, name='container_info'),
        path('servers/<int:server_id>/whitelist/', views_api.whitelist_list, name='whitelist_list'),
        path('servers/<int:server_id>/whitelist/add/', views_api.whitelist_add, name='whitelist_add'),
        path('servers/<int:server_id>/whitelist/remove/', views_api.whitelist_remove, name='whitelist_remove'),
        
        # Configuración del servidor
        path('servers/<int:server_id>/settings/', views_settings.server_settings, name='server_settings'),
        path('servers/<int:server_id>/settings/update/', views_settings.server_settings_update, name='server_settings_update'),
        
        # Usuarios de Minecraft
        path('servers/<int:server_id>/users/', views_settings.minecraft_users_list, name='minecraft_users_list'),
        path('servers/<int:server_id>/users/create/', views_settings.minecraft_user_create, name='minecraft_user_create'),
        path('servers/<int:server_id>/users/set-password/', views_settings.minecraft_user_set_password, name='minecraft_user_set_password'),
        path('servers/<int:server_id>/users/<int:user_id>/update/', views_settings.minecraft_user_update, name='minecraft_user_update'),
        path('servers/<int:server_id>/users/<int:user_id>/delete/', views_settings.minecraft_user_delete, name='minecraft_user_delete'),
        
        # Backups
        path('servers/<int:server_id>/backups/', views_backup.backups_list, name='backups_list'),
        path('servers/<int:server_id>/backups/create/', views_backup.backup_create, name='backup_create'),
        path('servers/<int:server_id>/backups/<int:backup_id>/restore/', views_backup.backup_restore, name='backup_restore'),
        path('servers/<int:server_id>/backup-schedules/', views_backup.backup_schedules_list, name='backup_schedules_list'),
        
        # Versiones de Minecraft
        path('minecraft/versions/', views_versions.available_versions, name='available_versions'),
        path('minecraft/versions/latest/', views_versions.latest_version, name='latest_version'),
        path('minecraft/versions/create/', views_versions.create_version, name='create_version'),
    ])),
    
    # Rutas legacy para compatibilidad (templates Django)
    path('login/', views_auth.LoggedLoginView.as_view(template_name='panel/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Páginas Django (deben ir antes del catch-all del frontend)
    path('control/', views_pages.control_page, name='control_page'),
    path('players/', views_pages.players_page, name='players_page'),
    path('mods/', views_pages.mods_page, name='mods_page'),
    path('settings/', views_pages.settings_page, name='settings_page'),
    path('logs/', views_pages.logs_page, name='logs_page'),
    
    # Servir archivos estáticos del frontend (JS, CSS, imágenes, etc.) ANTES del catch-all
    # Usar vista personalizada para MIME types correctos
] + ([re_path(r'^(.+\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|json))$', serve_frontend_static)] 
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / 'index.html').exists() else []) + [
    
    # Si existe frontend compilado, servirlo; si no, usar templates Django
    # Excluir api, admin, static, media, login, logout, control, players, mods, settings, logs y archivos estáticos
    re_path(r'^(?!api|admin|static|media|login|logout|control|players|mods|settings|logs|.*\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|json)).*$', serve, {
        'document_root': str(FRONTEND_DIST),
        'path': 'index.html'
    }) if FRONTEND_DIST.exists() and (FRONTEND_DIST / 'index.html').exists() else path('', views.dashboard, name='dashboard'),
]


# Servir archivos estáticos de Django (admin, etc.) - solo en modo DEBUG
from django.conf import settings
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
