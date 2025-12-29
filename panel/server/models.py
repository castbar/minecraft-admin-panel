from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
import hashlib
import secrets

# Importar todos los modelos de módulos separados
from .models_backup import Backup, BackupSchedule
from .models_stats import ServerStatistic, ServerEvent
from .models_security import IPWhitelist, IPBlacklist, RateLimitRule, SecurityLog
from .models_community import Ticket, TicketComment, PlayerRanking
from .models_multi import ServerSession, UserPreference

class Server(models.Model):
    """Modelo para servidores Minecraft"""
    AUTH_MODE_CHOICES = [
        ('whitelist', 'Solo Whitelist'),
        ('database', 'Base de Datos (usuarios y contraseñas)'),
        ('both', 'Whitelist + Base de Datos'),
        ('public', 'Público (sin autenticación)'),
    ]
    
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255, help_text="DNS, IP o nombre del contenedor Docker")
    container_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Nombre del contenedor Docker (si es diferente del host)"
    )
    rcon_port = models.IntegerField(default=25575)
    rcon_password = models.CharField(max_length=255)
    minecraft_data_path = models.CharField(max_length=500, default='/data')
    is_active = models.BooleanField(default=True)
    
    # Configuración de visibilidad y autenticación
    is_public = models.BooleanField(default=False, help_text="Servidor público (cualquiera puede conectarse)")
    is_hidden = models.BooleanField(
        default=False, 
        help_text="Servidor oculto (solo visible en misma red/VPN)"
    )
    auth_mode = models.CharField(
        max_length=20, 
        choices=AUTH_MODE_CHOICES, 
        default='whitelist',
        help_text="Modo de autenticación del servidor"
    )
    enable_whitelist = models.BooleanField(default=True, help_text="Habilitar whitelist en el servidor")
    online_mode = models.BooleanField(
        default=False, 
        help_text="Modo online (verifica con Mojang). Si False, permite clientes no premium"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Sincronizar configuración con el servidor Minecraft"""
        super().save(*args, **kwargs)
        # TODO: Aplicar cambios al servidor vía RCON o archivos de configuración
    
    def get_auth_mode_display_short(self):
        """Obtener descripción corta del modo de autenticación"""
        return dict(self.AUTH_MODE_CHOICES).get(self.auth_mode, self.auth_mode)

class UserServerRole(models.Model):
    """Roles de usuarios en servidores"""
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('moderator', 'Moderador'),
        ('viewer', 'Visualizador'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'server']

    def __str__(self):
        return f"{self.user.username} - {self.server.name} ({self.role})"

    def has_permission(self, permission):
        """Verificar si el usuario tiene un permiso específico"""
        permissions = {
            'admin': ['view', 'manage_whitelist', 'manage_mods', 'control_server', 'view_logs', 'execute_commands', 'manage_users', 'manage_settings'],
            'moderator': ['view', 'manage_whitelist', 'view_logs', 'execute_commands'],
            'viewer': ['view', 'view_logs'],
        }
        return permission in permissions.get(self.role, [])

class MinecraftUser(models.Model):
    """Usuarios de Minecraft para autenticación en base de datos"""
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='minecraft_users')
    username = models.CharField(max_length=16, validators=[MinLengthValidator(3)])
    password_hash = models.CharField(max_length=255)  # Hash de la contraseña
    salt = models.CharField(max_length=32)  # Salt para el hash
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['server', 'username']
        indexes = [
            models.Index(fields=['server', 'username']),
        ]

    def __str__(self):
        return f"{self.username}@{self.server.name}"
    
    def set_password(self, raw_password):
        """Establecer contraseña con hash seguro"""
        self.salt = secrets.token_hex(16)
        password_with_salt = f"{raw_password}{self.salt}"
        self.password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    def check_password(self, raw_password):
        """Verificar contraseña"""
        password_with_salt = f"{raw_password}{self.salt}"
        password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
        return password_hash == self.password_hash
    
    @classmethod
    def authenticate(cls, server, username, password):
        """Autenticar usuario de Minecraft"""
        try:
            user = cls.objects.get(server=server, username=username, is_active=True)
            if user.check_password(password):
                user.last_login = models.DateTimeField(auto_now=True)
                user.save(update_fields=['last_login'])
                return user
        except cls.DoesNotExist:
            pass
        return None
