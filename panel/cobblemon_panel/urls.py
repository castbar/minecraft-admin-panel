"""
URL configuration for cobblemon_panel project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from server import views, views_api, views_settings, views_backup, views_auth, views_docker, views_pages

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views_auth.LoggedLoginView.as_view(template_name='panel/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),  # Dashboard detecta servidor automáticamente
    
    # Páginas separadas
    path('mods/', views_pages.mods_page, name='mods_page'),
    path('players/', views_pages.players_page, name='players_page'),
    path('logs/', views_pages.logs_page, name='logs_page'),
    path('control/', views_pages.control_page, name='control_page'),
    path('settings/', views_pages.settings_page, name='settings_page'),
    
    # API de autenticación para app móvil
    path('api/auth/login/', views_auth.api_login, name='api_login'),
    
    # API multi-servidor
    path('api/servers/switch/', views_api.switch_server, name='switch_server'),
    path('api/servers/sessions/', views_api.saved_sessions, name='saved_sessions'),
    
    # Logs de seguridad
    path('api/security/logs/', views_api.security_logs, name='security_logs'),
    
    # API antigua (compatibilidad)
    path('api/whitelist/', views.whitelist_api, name='whitelist_api'),
    path('api/whitelist/<str:action>/', views.whitelist_action, name='whitelist_action'),
    path('api/mods/', views.mods_api, name='mods_api'),
    path('api/mods/<str:action>/', views.mods_action, name='mods_action'),
    path('api/players/', views.players_api, name='players_api'),
    path('api/logs/', views.logs_api, name='logs_api'),
    path('api/command/', views.command_api, name='command_api'),
    
    # API nueva (multi-servidor con roles)
    path('api/servers/', views_api.servers_list, name='servers_list'),
    path('api/servers/create/', views_docker.create_server, name='create_server'),
    path('api/servers/<int:server_id>/status/', views_api.server_status, name='server_status'),
    path('api/servers/<int:server_id>/stats/', views_api.server_stats, name='server_stats'),
    path('api/servers/<int:server_id>/control/<str:action>/', views_api.server_control, name='server_control'),
    path('api/servers/<int:server_id>/container/', views_docker.container_info, name='container_info'),
    path('api/servers/<int:server_id>/whitelist/', views_api.whitelist_list, name='whitelist_list'),
    path('api/servers/<int:server_id>/whitelist/add/', views_api.whitelist_add, name='whitelist_add'),
    path('api/servers/<int:server_id>/whitelist/remove/', views_api.whitelist_remove, name='whitelist_remove'),
    
    # Configuración del servidor
    path('api/servers/<int:server_id>/settings/', views_settings.server_settings, name='server_settings'),
    path('api/servers/<int:server_id>/settings/update/', views_settings.server_settings_update, name='server_settings_update'),
    
    # Usuarios de Minecraft (autenticación en base de datos)
    path('api/servers/<int:server_id>/users/', views_settings.minecraft_users_list, name='minecraft_users_list'),
    path('api/servers/<int:server_id>/users/create/', views_settings.minecraft_user_create, name='minecraft_user_create'),
    path('api/servers/<int:server_id>/users/<int:user_id>/update/', views_settings.minecraft_user_update, name='minecraft_user_update'),
    path('api/servers/<int:server_id>/users/<int:user_id>/delete/', views_settings.minecraft_user_delete, name='minecraft_user_delete'),
    
    # Backups
    path('api/servers/<int:server_id>/backups/', views_backup.backups_list, name='backups_list'),
    path('api/servers/<int:server_id>/backups/create/', views_backup.backup_create, name='backup_create'),
    path('api/servers/<int:server_id>/backups/<int:backup_id>/restore/', views_backup.backup_restore, name='backup_restore'),
    path('api/servers/<int:server_id>/backup-schedules/', views_backup.backup_schedules_list, name='backup_schedules_list'),
]

