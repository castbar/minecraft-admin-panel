"""
Comando para poblar el pool de mods con los más populares
Ejecutar: python manage.py populate_mods_pool
"""
from django.core.management.base import BaseCommand
from server.models.models_mods_pool import ModPool

class Command(BaseCommand):
    help = 'Poblar el pool de mods con los más populares y útiles'

    def handle(self, *args, **options):
        mods_data = [
            # Mods de Fabric/Forge
            {
                'name': 'Cobblemon-fabric-1.7.1+1.21.1',
                'display_name': 'Cobblemon',
                'mod_type': 'mod',
                'compatible_fabric': True,
                'compatible_forge': True,
                'description': 'Mod de Pokémon para Minecraft - captura, entrena y lucha con Pokémon',
                'category': 'pokemon',
                'version': '1.20.1',
                'is_popular': True,
                'is_recommended': True,
                'config_file_path': 'config/cobblemon.json',
                'config_format': 'json',
                'default_config': '{\n  "spawnRate": 0.5,\n  "enableShiny": true,\n  "maxPokemonPerChunk": 5\n}',
            },
            {
                'name': 'voicechat-fabric-1.21.1-2.6.10',
                'display_name': 'Simple Voice Chat',
                'mod_type': 'mod',
                'compatible_fabric': True,
                'compatible_forge': True,
                'description': 'Chat de voz por proximidad - comunicación por voz en el juego',
                'category': 'voice',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': True,
                'config_file_path': 'config/simple-voice-chat.json',
                'config_format': 'json',
                'default_config': '{\n  "voiceChat": {\n    "maxPriorityDistance": 48.0,\n    "minPriorityDistance": 8.0,\n    "fadeDistance": 16.0,\n    "enableVoiceActivation": true,\n    "enableSpatialAudio": true,\n    "enableWhisperDistance": true,\n    "whisperDistance": 4.0,\n    "shoutDistance": 96.0\n  },\n  "server": {\n    "port": 24477,\n    "bindAddress": "0.0.0.0",\n    "enableUdp": true,\n    "enableTcp": true\n  }\n}',
            },
            {
                'name': 'jei',
                'display_name': 'JEI (Just Enough Items)',
                'mod_type': 'mod',
                'compatible_fabric': True,
                'compatible_forge': True,
                'description': 'Ver recetas de items y usos - esencial para modpacks',
                'category': 'utility',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': True,
                'config_file_path': 'config/jei/jei-client.toml',
                'config_format': 'toml',
                'default_config': '[general]\nsearchMode = "normal"\nmaxSearchResults = 100',
            },
            {
                'name': 'wthit',
                'display_name': 'WTHIT (What The Hell Is That)',
                'mod_type': 'mod',
                'compatible_fabric': True,
                'compatible_forge': False,
                'description': 'Información de bloques y entidades al mirar - reemplazo de Waila/HWYLA',
                'category': 'utility',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': False,
                'config_file_path': 'config/wthit.json',
                'config_format': 'json',
                'default_config': '{\n  "showEntityInfo": true,\n  "showBlockInfo": true\n}',
            },
            {
                'name': 'fabric-api',
                'display_name': 'Fabric API',
                'mod_type': 'mod',
                'compatible_fabric': True,
                'compatible_forge': False,
                'description': 'API requerida para la mayoría de mods de Fabric',
                'category': 'core',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': True,
                'config_file_path': '',
                'config_format': 'json',
                'default_config': '',
            },
            # Plugins de Bukkit/Spigot/Paper
            {
                'name': 'luckperms',
                'display_name': 'LuckPerms',
                'mod_type': 'plugin',
                'compatible_bukkit': True,
                'compatible_spigot': True,
                'compatible_paper': True,
                'description': 'Sistema de permisos avanzado - el mejor sistema de permisos para servidores',
                'category': 'permissions',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': True,
                'config_file_path': 'plugins/LuckPerms/config.yml',
                'config_format': 'yaml',
                'default_config': 'server: default\nstorage-method: h2\ndata:\n  address: localhost:3306',
            },
            {
                'name': 'worldedit',
                'display_name': 'WorldEdit',
                'mod_type': 'plugin',
                'compatible_bukkit': True,
                'compatible_spigot': True,
                'compatible_paper': True,
                'description': 'Edición rápida de mundos - herramienta esencial para construcción',
                'category': 'building',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': False,
                'config_file_path': 'plugins/WorldEdit/config.yml',
                'config_format': 'yaml',
                'default_config': 'max-blocks-changed:\n  default: 32768\n  maximum: -1',
            },
            {
                'name': 'essentialsx',
                'display_name': 'EssentialsX',
                'mod_type': 'plugin',
                'compatible_bukkit': True,
                'compatible_spigot': True,
                'compatible_paper': True,
                'description': 'Comandos esenciales para servidores - teleport, home, warp, etc.',
                'category': 'utility',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': True,
                'config_file_path': 'plugins/Essentials/config.yml',
                'config_format': 'yaml',
                'default_config': 'locale: en\nserver-name: Minecraft Server',
            },
            {
                'name': 'simple-voice-chat-plugin',
                'display_name': 'Simple Voice Chat (Plugin)',
                'mod_type': 'plugin',
                'compatible_bukkit': True,
                'compatible_spigot': True,
                'compatible_paper': True,
                'description': 'Chat de voz por proximidad (versión plugin) - solo servidor, jugadores no necesitan mod',
                'category': 'voice',
                'version': 'latest',
                'is_popular': True,
                'is_recommended': True,
                'config_file_path': 'plugins/simple-voice-chat/config.yml',
                'config_format': 'yaml',
                'default_config': 'voice:\n  distance: 48.0\n  fadeDistance: 16.0\n  whisperDistance: 4.0\n  shoutDistance: 96.0\nserver:\n  port: 24477',
            },
        ]
        
        created = 0
        updated = 0
        
        for mod_data in mods_data:
            mod, created_flag = ModPool.objects.update_or_create(
                name=mod_data['name'],
                defaults=mod_data
            )
            if created_flag:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Creado: {mod.display_name}'))
            else:
                updated += 1
                self.stdout.write(self.style.WARNING(f'⚠️  Actualizado: {mod.display_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Pool poblado: {created} creados, {updated} actualizados'))

