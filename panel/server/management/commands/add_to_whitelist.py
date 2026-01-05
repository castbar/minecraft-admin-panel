"""
Comando para agregar usuarios a la whitelist de un servidor
Ejecutar: python manage.py add_to_whitelist <username> --server-id <id>
         python manage.py add_to_whitelist <username> --server-name <name>
"""
from django.core.management.base import BaseCommand, CommandError
from server.models import Server
from server.views.views_api import _get_rcon_connection
from server.models.models_security import SecurityLog
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Agregar usuario a la whitelist de un servidor'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre del usuario de Minecraft a agregar')
        parser.add_argument(
            '--server-id',
            type=int,
            help='ID del servidor'
        )
        parser.add_argument(
            '--server-name',
            type=str,
            help='Nombre del servidor (buscará por nombre parcial)'
        )
        parser.add_argument(
            '--list-failed',
            action='store_true',
            help='Listar intentos de login fallidos recientes relacionados con whitelist'
        )
        parser.add_argument(
            '--search',
            type=str,
            help='Buscar usuarios que contengan este texto en los logs recientes'
        )

    def handle(self, *args, **options):
        # Si se solicita listar fallos o buscar
        if options['list_failed'] or options['search']:
            self.list_failed_attempts(options.get('search'))
            return

        username = options['username']
        server_id = options.get('server_id')
        server_name = options.get('server_name')

        # Obtener servidor
        server = None
        if server_id:
            try:
                server = Server.objects.get(id=server_id, is_active=True)
            except Server.DoesNotExist:
                raise CommandError(f'Servidor con ID {server_id} no encontrado')
        elif server_name:
            servers = Server.objects.filter(
                name__icontains=server_name,
                is_active=True
            )
            if servers.count() == 0:
                raise CommandError(f'No se encontró ningún servidor con nombre que contenga "{server_name}"')
            elif servers.count() > 1:
                self.stdout.write(self.style.WARNING(f'Se encontraron {servers.count()} servidores:'))
                for s in servers:
                    self.stdout.write(f'  - ID {s.id}: {s.name} ({s.host})')
                raise CommandError('Hay múltiples servidores. Usa --server-id para especificar')
            else:
                server = servers.first()
        else:
            # Si no se especifica servidor, mostrar lista de servidores activos
            servers = Server.objects.filter(is_active=True)
            if servers.count() == 0:
                raise CommandError('No hay servidores activos')
            elif servers.count() == 1:
                server = servers.first()
                self.stdout.write(self.style.WARNING(f'Usando único servidor activo: {server.name} (ID: {server.id})'))
            else:
                self.stdout.write(self.style.WARNING('Servidores activos disponibles:'))
                for s in servers:
                    self.stdout.write(f'  - ID {s.id}: {s.name} ({s.host})')
                raise CommandError('Especifica --server-id o --server-name para seleccionar un servidor')

        # Agregar usuario a whitelist
        self.stdout.write(f'Agregando usuario "{username}" a whitelist del servidor "{server.name}"...')
        
        rcon = _get_rcon_connection(server)
        if rcon is None:
            raise CommandError(
                f'No se pudo conectar a RCON. '
                f'Host: {server.host}, Puerto: {server.rcon_port}'
            )

        try:
            response = rcon.command(f'whitelist add {username}')
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario "{username}" agregado a whitelist'))
            self.stdout.write(f'Respuesta del servidor: {response}')
            
            # Registrar en logs
            from server.models.models_security import SecurityLog
            SecurityLog.objects.create(
                log_type='suspicious_activity',
                ip_address='127.0.0.1',
                details={
                    'message': f'Usuario {username} agregado a whitelist mediante comando de gestión',
                    'username': username,
                    'server': server.name,
                    'action': 'whitelist_add'
                }
            )
        except Exception as e:
            raise CommandError(f'Error al agregar usuario a whitelist: {str(e)}')
        finally:
            try:
                rcon.disconnect()
            except:
                pass

    def list_failed_attempts(self, search_term=None):
        """Listar intentos de login fallidos recientes"""
        self.stdout.write(self.style.WARNING('\n=== Intentos de Login Fallidos Recientes (últimas 24 horas) ===\n'))
        
        # Buscar logs de fallos recientes (últimas 24 horas)
        since = timezone.now() - timedelta(hours=24)
        logs = SecurityLog.objects.filter(
            log_type='failed_login',
            created_at__gte=since
        ).order_by('-created_at')[:50]

        if not logs.exists():
            self.stdout.write('No se encontraron intentos de login fallidos en las últimas 24 horas.')
            return

        # Filtrar por término de búsqueda si se proporciona
        if search_term:
            logs = logs.filter(
                details__username__icontains=search_term
            ) | logs.filter(
                details__message__icontains=search_term
            )

        if not logs.exists():
            self.stdout.write(f'No se encontraron logs que contengan "{search_term}"')
            return

        for log in logs:
            username = log.details.get('username', 'desconocido')
            message = log.details.get('message', '')
            self.stdout.write(
                f'[{log.created_at.strftime("%Y-%m-%d %H:%M:%S")}] '
                f'Usuario: {self.style.WARNING(username)} | '
                f'IP: {log.ip_address} | '
                f'Mensaje: {message}'
            )

        self.stdout.write(f'\nTotal: {logs.count()} intentos encontrados\n')
        
        # Sugerir comando para agregar
        if search_term:
            self.stdout.write(self.style.SUCCESS(
                f'\n💡 Para agregar un usuario a la whitelist, usa:\n'
                f'   python manage.py add_to_whitelist <username> --server-id <id>'
            ))


