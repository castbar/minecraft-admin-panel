from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
import hashlib
import secrets
import uuid

# Importar todos los modelos de módulos separados
from .models_backup import Backup, BackupSchedule
from .models_stats import ServerStatistic, ServerEvent
from .models_security import IPWhitelist, IPBlacklist, RateLimitRule, SecurityLog
from .models_community import Ticket, TicketComment, PlayerRanking
from .models_multi import ServerSession, UserPreference
from .models_mods import ModConfigTemplate, ServerModConfig
from .models_mods_pool import ModPool

class Server(models.Model):
    """Modelo para servidores Minecraft"""
    AUTH_MODE_CHOICES = [
        ('whitelist', 'Solo Whitelist'),
        ('database', 'Base de Datos (usuarios y contraseñas)'),
        ('both', 'Whitelist + Base de Datos'),
        ('public', 'Público (sin autenticación)'),
    ]
    
    SERVER_TYPE_CHOICES = [
        ('vanilla', 'Vanilla (oficial)'),
        ('fabric', 'Fabric'),
        ('forge', 'Forge'),
        ('bukkit', 'Bukkit'),
        ('spigot', 'Spigot'),
        ('paper', 'Paper'),
    ]
    
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255, help_text="DNS, IP o nombre del contenedor Docker")
    container_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Nombre del contenedor Docker (si es diferente del host)"
    )
    port = models.IntegerField(default=25565, help_text="Puerto del servidor Minecraft")
    rcon_port = models.IntegerField(default=25575)
    rcon_password = models.CharField(max_length=255)
    minecraft_data_path = models.CharField(max_length=500, default='/data')
    # Puertos adicionales para mods/plugins (ej: Simple Voice Chat necesita UDP 24454)
    # Formato: [{"port": 24454, "protocol": "udp", "host_port": 24454}, ...]
    additional_ports = models.JSONField(
        default=list,
        blank=True,
        help_text="Puertos adicionales a exponer. Formato: [{'port': 24454, 'protocol': 'udp', 'host_port': 24454}]"
    )
    is_active = models.BooleanField(default=True)
    
    # Tipo de servidor y versión
    server_type = models.CharField(
        max_length=20,
        choices=SERVER_TYPE_CHOICES,
        default='vanilla',
        help_text="Tipo de servidor Minecraft"
    )
    minecraft_version = models.CharField(
        max_length=20,
        default='latest',
        help_text="Versión de Minecraft (ej: 1.20.1, latest)"
    )
    
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
    api_key = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="API key para autenticación del plugin/mod (se genera automáticamente)"
    )
    online_mode = models.BooleanField(
        default=False, 
        help_text="Modo online (verifica con Mojang). Si False, permite clientes no premium"
    )
    
    # Mods y plugins base
    install_fabric_api = models.BooleanField(
        default=False,
        help_text="Instalar Fabric API (requerido para mods de Fabric)"
    )
    install_forge = models.BooleanField(
        default=False,
        help_text="Instalar Forge (requerido para mods de Forge)"
    )
    install_luckperms = models.BooleanField(
        default=False,
        help_text="Instalar LuckPerms (sistema de permisos)"
    )
    install_worldedit = models.BooleanField(
        default=False,
        help_text="Instalar WorldEdit (edición de mundos)"
    )
    install_proximity_chat = models.BooleanField(
        default=False,
        help_text="Instalar chat de proximidad (voice/chat por distancia)"
    )
    install_spark = models.BooleanField(
        default=True,
        help_text="Instalar Spark (profiling y análisis de rendimiento)"
    )
    install_more_inventory = models.BooleanField(
        default=False,
        help_text="Instalar Más Mochila (More Inventory) - aumenta inventario del jugador"
    )
    install_jei = models.BooleanField(
        default=False,
        help_text="Instalar JEI/REI (Just Enough Items) - ver recetas de items"
    )
    install_wthit = models.BooleanField(
        default=False,
        help_text="Instalar WTHIT (What The Hell Is That) - información de bloques"
    )
    install_essentials = models.BooleanField(
        default=False,
        help_text="Instalar EssentialsX (comandos esenciales) - solo para Bukkit/Spigot/Paper"
    )
    
    # Configuración adicional
    additional_mods = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de mods adicionales a instalar (nombres de archivos)"
    )
    additional_plugins = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de plugins adicionales a instalar (nombres de archivos)"
    )
    
    # Configuración de memoria y Java
    memory_limit_mb = models.IntegerField(
        default=2048,
        help_text="Límite de memoria RAM en MB (ej: 2048 = 2GB)"
    )
    java_heap_min_mb = models.IntegerField(
        default=512,
        help_text="Heap mínimo de Java en MB (Xms)"
    )
    java_heap_max_mb = models.IntegerField(
        default=1536,
        help_text="Heap máximo de Java en MB (Xmx) - debe ser < memory_limit_mb"
    )
    java_gc_type = models.CharField(
        max_length=20,
        choices=[
            ('g1', 'G1GC (recomendado para >2GB)'),
            ('parallel', 'ParallelGC (para <2GB)'),
            ('zgc', 'ZGC (experimental, Java 17+)'),
        ],
        default='g1',
        help_text="Tipo de Garbage Collector"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Sincronizar configuración con el servidor Minecraft"""
        # Generar API key si no existe y se necesita para database/both
        if self.auth_mode in ['database', 'both'] and not self.api_key:
            self.generate_api_key()
        super().save(*args, **kwargs)
        # TODO: Aplicar cambios al servidor vía RCON o archivos de configuración
    
    def get_auth_mode_display_short(self):
        """Obtener descripción corta del modo de autenticación"""
        return dict(self.AUTH_MODE_CHOICES).get(self.auth_mode, self.auth_mode)
    
    def generate_api_key(self):
        """Generar API key única para el servidor"""
        if not self.api_key:
            self.api_key = uuid.uuid4().hex
        return self.api_key
    
    def verify_api_key(self, provided_key):
        """Verificar API key"""
        return self.api_key and self.api_key == provided_key

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
    email = models.EmailField(null=True, blank=True, help_text="Email del usuario para envío de token de contraseña")
    password_hash = models.CharField(max_length=255, blank=True, null=True)  # Hash de la contraseña (null hasta que se establezca)
    salt = models.CharField(max_length=32, blank=True, null=True)  # Salt para el hash
    is_active = models.BooleanField(default=False, help_text="Activo solo después de establecer contraseña")
    password_set_token = models.CharField(max_length=64, blank=True, null=True, help_text="Token para establecer contraseña")
    password_set_token_expires = models.DateTimeField(null=True, blank=True, help_text="Expiración del token (24 horas)")
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
        if not self.password_hash or not self.salt:
            return False  # Usuario no tiene contraseña establecida
        password_with_salt = f"{raw_password}{self.salt}"
        password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
        return password_hash == self.password_hash
    
    def generate_password_set_token(self):
        """Generar token para establecer contraseña"""
        from django.utils import timezone
        from datetime import timedelta
        import secrets
        
        self.password_set_token = secrets.token_urlsafe(32)
        self.password_set_token_expires = timezone.now() + timedelta(hours=24)
        # Guardar todos los campos si no tiene ID, o solo los campos del token si ya existe
        if self.pk:
            self.save(update_fields=['password_set_token', 'password_set_token_expires'])
        else:
            self.save()  # Guardar completo si es nuevo
        return self.password_set_token
    
    def is_password_set_token_valid(self, token):
        """Verificar si el token es válido"""
        from django.utils import timezone
        
        if not self.password_set_token or not self.password_set_token_expires:
            return False
        
        if self.password_set_token != token:
            return False
        
        if timezone.now() > self.password_set_token_expires:
            return False
        
        return True
    
    def has_password_set(self):
        """Verificar si el usuario ya tiene contraseña establecida"""
        return bool(self.password_hash and self.salt)
    
    @classmethod
    def authenticate(cls, server, username, password):
        """Autenticar usuario de Minecraft"""
        try:
            user = cls.objects.get(server=server, username=username, is_active=True)
            if not user.has_password_set():
                return None  # Usuario no ha establecido contraseña aún
            if user.check_password(password):
                from django.utils import timezone
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                return user
        except cls.DoesNotExist:
            pass
        return None
