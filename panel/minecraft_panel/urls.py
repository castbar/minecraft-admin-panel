"""
URL configuration for minecraft_panel project.

NOTA: El frontend Ionic se sirve desde Nginx (servicio minecraft-admin-frontend).
Django solo maneja APIs, admin y autenticación.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from server.views import views, views_api, views_settings, views_backup, views_auth, views_docker, views_versions, views_mods, views_mods_config, views_mods_config_simple, views_mods_pool, views_users

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints (deben ir antes del catch-all del frontend)
    path('api/', include([
        # API de autenticación
        path('auth/login/', views_auth.api_login, name='api_login'),
        path('auth/check/', views_auth.api_check_auth, name='api_check_auth'),
        path('servers/<int:server_id>/auth/', views_auth.minecraft_user_authenticate, name='minecraft_user_authenticate'),
        
        # API multi-servidor
        path('servers/switch/', views_api.switch_server, name='switch_server'),
        path('servers/sessions/', views_api.saved_sessions, name='saved_sessions'),
        path('security/logs/', views_api.security_logs, name='security_logs'),
        
        # Pool de mods precargados (debe ir antes de /mods/ para evitar conflictos)
        path('mods/pool/', views_mods_pool.mods_pool_list, name='mods_pool_list'),
        path('mods/pool/categories/', views_mods_pool.mods_pool_categories, name='mods_pool_categories'),
        path('mods/pool/<int:mod_id>/', views_mods_pool.mods_pool_detail, name='mods_pool_detail'),
        path('mods/pool/create/', views_mods_pool.mods_pool_create, name='mods_pool_create'),
        path('servers/<int:server_id>/mods/pool/install/', views_mods_pool.mods_pool_install, name='mods_pool_install'),
        
        # API antigua (compatibilidad)
        path('whitelist/', views.whitelist_api, name='whitelist_api'),
        path('whitelist/<str:action>/', views.whitelist_action, name='whitelist_action'),
        path('mods/', views.mods_api, name='mods_api'),
        path('mods/<str:action>/', views.mods_action, name='mods_action'),
        path('players/', views.players_api, name='players_api'),
        path('servers/<int:server_id>/players/online/', views_api.players_online, name='players_online'),
        path('logs/', views.logs_api, name='logs_api'),
        path('command/', views.command_api, name='command_api'),
        
        # API de mods (nueva estructura)
        path('servers/<int:server_id>/mods/', views_mods.mods_list, name='mods_list'),
        path('servers/<int:server_id>/mods/upload/', views_mods.mod_upload, name='mod_upload'),
        path('servers/<int:server_id>/mods/enable/', views_mods.mod_enable, name='mod_enable'),
        path('servers/<int:server_id>/mods/disable/', views_mods.mod_disable, name='mod_disable'),
        path('servers/<int:server_id>/mods/delete/', views_mods.mod_delete, name='mod_delete'),
        
        # API de configuración de mods (simplificada - desde gestión de mods)
        path('servers/<int:server_id>/mods/config/', views_mods_config_simple.mod_config_get, name='mod_config_get'),
        path('servers/<int:server_id>/mods/config/update/', views_mods_config_simple.mod_config_update, name='mod_config_update'),
        path('servers/<int:server_id>/mods/config/reset/', views_mods_config_simple.mod_config_reset, name='mod_config_reset'),
        
        # API de configuraciones de mods (plantillas globales)
        path('mods/templates/', views_mods_config.mod_templates_list, name='mod_templates_list'),
        path('mods/templates/<int:template_id>/', views_mods_config.mod_template_detail, name='mod_template_detail'),
        path('mods/templates/create/', views_mods_config.mod_template_create, name='mod_template_create'),
        path('mods/templates/<int:template_id>/update/', views_mods_config.mod_template_update, name='mod_template_update'),
        
        # API de configuraciones de mods por servidor
        path('servers/<int:server_id>/mods/configs/', views_mods_config.server_mod_configs_list, name='server_mod_configs_list'),
        path('servers/<int:server_id>/mods/configs/create/', views_mods_config.server_mod_config_create, name='server_mod_config_create'),
        path('servers/<int:server_id>/mods/configs/<int:config_id>/', views_mods_config.server_mod_config_detail, name='server_mod_config_detail'),
        path('servers/<int:server_id>/mods/configs/<int:config_id>/update/', views_mods_config.server_mod_config_update, name='server_mod_config_update'),
        path('servers/<int:server_id>/mods/configs/<int:config_id>/delete/', views_mods_config.server_mod_config_delete, name='server_mod_config_delete'),
        path('servers/<int:server_id>/mods/configs/<int:config_id>/apply/', views_mods_config.server_mod_config_apply, name='server_mod_config_apply'),
        path('servers/<int:server_id>/mods/configs/apply-all/', views_mods_config.server_mod_configs_apply_all, name='server_mod_configs_apply_all'),
        
        # API nueva (multi-servidor con roles)
        path('servers/', views_api.servers_list, name='servers_list'),
        path('servers/create/', views_docker.create_server, name='create_server'),
        path('servers/<int:server_id>/delete/', views_docker.delete_server, name='delete_server'),
        path('servers/<int:server_id>/status/', views_api.server_status, name='server_status'),
        path('servers/<int:server_id>/stats/', views_api.server_stats, name='server_stats'),
        path('servers/<int:server_id>/logs/', views_api.server_logs, name='server_logs'),
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
        path('servers/<int:server_id>/backups/<int:backup_id>/download/', views_backup.backup_download, name='backup_download'),
        path('servers/<int:server_id>/backups/<int:backup_id>/delete/', views_backup.backup_delete, name='backup_delete'),
        path('servers/<int:server_id>/backup-schedules/', views_backup.backup_schedules_list, name='backup_schedules_list'),
        path('servers/<int:server_id>/backup-schedules/create/', views_backup.backup_schedule_create, name='backup_schedule_create'),
        path('servers/<int:server_id>/backup-schedules/<int:schedule_id>/update/', views_backup.backup_schedule_update, name='backup_schedule_update'),
        path('servers/<int:server_id>/backup-schedules/<int:schedule_id>/delete/', views_backup.backup_schedule_delete, name='backup_schedule_delete'),
        
        # Versiones de Minecraft
        path('minecraft/versions/', views_versions.available_versions, name='available_versions'),
        path('minecraft/versions/latest/', views_versions.latest_version, name='latest_version'),
        path('minecraft/versions/create/', views_versions.create_version, name='create_version'),
        
        # Gestión de usuarios Django (solo staff)
        path('users/', views_users.django_users_list, name='django_users_list'),
        path('users/create/', views_users.django_user_create, name='django_user_create'),
        path('users/<int:user_id>/', views_users.django_user_detail, name='django_user_detail'),
        path('users/<int:user_id>/update/', views_users.django_user_update, name='django_user_update'),
        path('users/<int:user_id>/delete/', views_users.django_user_delete, name='django_user_delete'),
        path('users/<int:user_id>/change-password/', views_users.django_user_change_password, name='django_user_change_password'),
        path('users/<int:user_id>/roles/', views_users.user_roles_list, name='user_roles_list'),
        path('users/me/permissions/', views_users.user_permissions, name='user_permissions'),
        
        # Gestión de roles en servidores
        path('servers/<int:server_id>/roles/', views_users.server_roles_list, name='server_roles_list'),
        path('servers/<int:server_id>/roles/assign/', views_users.server_role_assign, name='server_role_assign'),
        path('servers/<int:server_id>/roles/<int:role_id>/update/', views_users.server_role_update, name='server_role_update'),
        path('servers/<int:server_id>/roles/<int:role_id>/remove/', views_users.server_role_remove, name='server_role_remove'),
    ])),
    
    # Autenticación (login/logout - Nginx hace proxy a estas rutas)
    path('login/', views_auth.LoggedLoginView.as_view(template_name='panel/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]


# Servir archivos estáticos de Django (admin, etc.) - solo en modo DEBUG
from django.conf import settings
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
