from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from .models import (
    Server, UserServerRole, MinecraftUser,
    Backup, BackupSchedule,
    ServerStatistic, ServerEvent,
    IPWhitelist, IPBlacklist, RateLimitRule, SecurityLog,
    Ticket, TicketComment, PlayerRanking,
    MinecraftVersion
)

# Configurar branding de Castbar
admin.site.site_header = "Minecraft Server Manager"
admin.site.site_title = "Minecraft Server Manager"
admin.site.index_title = format_html(
    '<span style="color: #667eea; font-weight: bold;">Minecraft Server Manager</span> - '
    'Desarrollado por <span style="color: #764ba2; font-weight: bold;">Castbar</span>'
)

# Restringir acceso al admin solo a usuarios staff
def staff_required(user):
    """Verificar que el usuario es staff"""
    return user.is_authenticated and user.is_staff

# Sobrescribir el método de login del admin para redirigir usuarios no staff
original_admin_login = admin.site.login

@login_required
@user_passes_test(staff_required, login_url='/api/auth/login/')
def admin_login_required(request):
    """Redirigir usuarios no staff que intentan acceder al admin"""
    if not request.user.is_staff:
        # Redirigir al frontend (panel de Minecraft)
        return redirect('/')
    return original_admin_login(request)

# Personalizar el AdminSite para requerir staff
class StaffOnlyAdminSite(AdminSite):
    def has_permission(self, request):
        """Solo usuarios staff pueden acceder"""
        return request.user.is_active and request.user.is_staff

# Usar el AdminSite personalizado (opcional, Django admin ya verifica is_staff por defecto)
# admin.site = StaffOnlyAdminSite(name='admin')

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'container_name', 'is_public', 'is_hidden', 'auth_mode', 'enable_whitelist', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_public', 'is_hidden', 'auth_mode', 'enable_whitelist', 'created_at']
    search_fields = ['name', 'host', 'container_name']
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'host', 'container_name', 'rcon_port', 'rcon_password', 'minecraft_data_path')
        }),
        ('Configuración de Acceso', {
            'fields': ('is_public', 'is_hidden', 'auth_mode', 'enable_whitelist', 'online_mode'),
            'description': 'is_hidden: Solo visible en misma red/VPN'
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )

@admin.register(UserServerRole)
class UserServerRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'server', 'role', 'created_at']

@admin.register(MinecraftVersion)
class MinecraftVersionAdmin(admin.ModelAdmin):
    list_display = ['version', 'display_name', 'is_latest', 'is_stable', 'is_supported', 'release_date']
    list_filter = ['is_latest', 'is_stable', 'is_supported', 'release_date']
    search_fields = ['version', 'display_name']
    fieldsets = (
        ('Información Básica', {
            'fields': ('version', 'display_name', 'release_date')
        }),
        ('Estado', {
            'fields': ('is_latest', 'is_stable', 'is_supported')
        }),
        ('Compatibilidad', {
            'fields': ('server_types',),
            'description': 'Tipos de servidor compatibles: vanilla, fabric, forge, bukkit, spigot, paper'
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )

@admin.register(MinecraftUser)
class MinecraftUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'server', 'is_active', 'last_login', 'created_at']
    list_filter = ['is_active', 'server', 'created_at']
    search_fields = ['username', 'server__name']
    readonly_fields = ['password_hash', 'salt', 'last_login', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        """Hash de contraseña al guardar"""
        if 'password' in form.cleaned_data and form.cleaned_data['password']:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

# Backups
@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ['server', 'name', 'status', 'file_size', 'created_at']
    list_filter = ['status', 'server', 'created_at']
    search_fields = ['name', 'server__name']
    readonly_fields = ['file_path', 'file_size', 'status', 'error_message', 'created_at', 'completed_at']

@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = ['server', 'name', 'frequency', 'is_active', 'last_run']
    list_filter = ['frequency', 'is_active', 'storage_type']
    search_fields = ['name', 'server__name']

# Estadísticas
@admin.register(ServerStatistic)
class ServerStatisticAdmin(admin.ModelAdmin):
    list_display = ['server', 'timestamp', 'players_online', 'cpu_usage', 'memory_usage']
    list_filter = ['server', 'timestamp']
    readonly_fields = ['timestamp']

@admin.register(ServerEvent)
class ServerEventAdmin(admin.ModelAdmin):
    list_display = ['server', 'event_type', 'player_name', 'created_at']
    list_filter = ['event_type', 'server', 'created_at']
    search_fields = ['message', 'player_name']

# Seguridad
@admin.register(IPWhitelist)
class IPWhitelistAdmin(admin.ModelAdmin):
    list_display = ['server', 'ip_address', 'description', 'created_at']
    list_filter = ['server', 'created_at']
    search_fields = ['ip_address', 'description']

@admin.register(IPBlacklist)
class IPBlacklistAdmin(admin.ModelAdmin):
    list_display = ['server', 'ip_address', 'is_permanent', 'expires_at', 'created_at']
    list_filter = ['is_permanent', 'server', 'created_at']
    search_fields = ['ip_address', 'reason']

@admin.register(RateLimitRule)
class RateLimitRuleAdmin(admin.ModelAdmin):
    list_display = ['server', 'action', 'max_requests', 'time_window', 'is_active']
    list_filter = ['is_active', 'server']
    search_fields = ['action']

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ['server', 'log_type', 'ip_address', 'created_at']
    list_filter = ['log_type', 'server', 'created_at']
    search_fields = ['ip_address']
    readonly_fields = ['created_at']

# Comunidad
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['server', 'title', 'status', 'priority', 'created_by', 'created_at']
    list_filter = ['status', 'priority', 'server', 'created_at']
    search_fields = ['title', 'description']

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['message']

@admin.register(PlayerRanking)
class PlayerRankingAdmin(admin.ModelAdmin):
    list_display = ['server', 'player_name', 'metric', 'value', 'rank']
    list_filter = ['metric', 'server']
    search_fields = ['player_name']

