"""
Modelos para pool de mods precargados y compatibilidad
"""
from django.db import models
import json

class ModPool(models.Model):
    """
    Pool de mods precargados - mods más usados/útiles
    Incluye información de compatibilidad con tipos de servidor
    """
    MOD_TYPE_CHOICES = [
        ('mod', 'Mod (Fabric/Forge)'),
        ('plugin', 'Plugin (Bukkit/Spigot/Paper)'),
    ]
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Nombre del mod/plugin (ej: 'cobblemon', 'luckperms')"
    )
    display_name = models.CharField(
        max_length=255,
        help_text="Nombre para mostrar (ej: 'Cobblemon', 'LuckPerms')"
    )
    mod_type = models.CharField(
        max_length=20,
        choices=MOD_TYPE_CHOICES,
        help_text="Tipo: Mod (Fabric/Forge) o Plugin (Bukkit/Spigot/Paper)"
    )
    # Compatibilidad con tipos de servidor
    compatible_vanilla = models.BooleanField(
        default=False,
        help_text="Compatible con Vanilla (solo plugins nativos)"
    )
    compatible_fabric = models.BooleanField(
        default=False,
        help_text="Compatible con Fabric (solo mods)"
    )
    compatible_forge = models.BooleanField(
        default=False,
        help_text="Compatible con Forge (solo mods)"
    )
    compatible_bukkit = models.BooleanField(
        default=False,
        help_text="Compatible con Bukkit (solo plugins)"
    )
    compatible_spigot = models.BooleanField(
        default=False,
        help_text="Compatible con Spigot (solo plugins)"
    )
    compatible_paper = models.BooleanField(
        default=False,
        help_text="Compatible con Paper (solo plugins)"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Descripción del mod/plugin"
    )
    modrinth_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID en Modrinth (para mods) o SpigotMC (para plugins)"
    )
    curseforge_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID en CurseForge"
    )
    download_url = models.URLField(
        blank=True,
        help_text="URL directa de descarga (opcional)"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Ruta del archivo .jar en el servidor (ej: '/data/mods_pool/cobblemon.jar')"
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Versión recomendada (ej: '1.20.1', 'latest')"
    )
    is_popular = models.BooleanField(
        default=False,
        help_text="¿Es un mod/plugin popular?"
    )
    is_recommended = models.BooleanField(
        default=False,
        help_text="¿Es recomendado para nuevos servidores?"
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Categoría (ej: 'pokemon', 'voice', 'economy', 'permissions')"
    )
    config_file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Ruta del archivo de configuración (ej: 'config/cobblemon.json')"
    )
    config_format = models.CharField(
        max_length=20,
        choices=[
            ('json', 'JSON'),
            ('yaml', 'YAML'),
            ('properties', 'Properties'),
            ('toml', 'TOML'),
            ('txt', 'Texto plano'),
        ],
        default='json',
        help_text="Formato del archivo de configuración"
    )
    default_config = models.TextField(
        blank=True,
        help_text="Configuración por defecto (opcional)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="¿Está activo en el pool?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mod/Plugin del Pool"
        verbose_name_plural = "Mods/Plugins del Pool"
        ordering = ['-is_recommended', '-is_popular', 'display_name']
    
    def __str__(self):
        return f"{self.display_name} ({self.mod_type})"
    
    def get_compatible_server_types(self):
        """Obtener lista de tipos de servidor compatibles"""
        compatible = []
        if self.compatible_vanilla:
            compatible.append('vanilla')
        if self.compatible_fabric:
            compatible.append('fabric')
        if self.compatible_forge:
            compatible.append('forge')
        if self.compatible_bukkit:
            compatible.append('bukkit')
        if self.compatible_spigot:
            compatible.append('spigot')
        if self.compatible_paper:
            compatible.append('paper')
        return compatible
    
    def is_compatible_with(self, server_type):
        """Verificar si es compatible con un tipo de servidor"""
        compatibility_map = {
            'vanilla': self.compatible_vanilla,
            'fabric': self.compatible_fabric,
            'forge': self.compatible_forge,
            'bukkit': self.compatible_bukkit,
            'spigot': self.compatible_spigot,
            'paper': self.compatible_paper,
        }
        return compatibility_map.get(server_type, False)
    
    def get_config_dict(self):
        """Obtener configuración como diccionario (si es JSON)"""
        if self.config_format == 'json' and self.default_config:
            try:
                return json.loads(self.default_config)
            except json.JSONDecodeError:
                return {}
        return {}

