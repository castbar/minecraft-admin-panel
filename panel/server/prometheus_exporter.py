from prometheus_client import Counter, Gauge, Histogram, start_http_server
from .models import Server, ServerStatistic
import time
import threading

# Métricas Prometheus
players_online = Gauge('minecraft_players_online', 'Players online', ['server_name'])
server_online = Gauge('minecraft_server_online', 'Server online status', ['server_name'])
cpu_usage = Gauge('minecraft_server_cpu_usage', 'CPU usage percentage', ['server_name'])
memory_usage = Gauge('minecraft_server_memory_usage', 'Memory usage in bytes', ['server_name'])
tps = Gauge('minecraft_server_tps', 'Ticks per second', ['server_name'])

def update_metrics():
    """Actualizar métricas desde base de datos"""
    servers = Server.objects.filter(is_active=True)
    
    for server in servers:
        try:
            # Obtener última estadística
            stat = ServerStatistic.objects.filter(server=server).latest('timestamp')
            
            players_online.labels(server_name=server.name).set(stat.players_online)
            server_online.labels(server_name=server.name).set(1 if stat.players_online >= 0 else 0)
            
            if stat.cpu_usage:
                cpu_usage.labels(server_name=server.name).set(stat.cpu_usage)
            if stat.memory_usage:
                memory_usage.labels(server_name=server.name).set(stat.memory_usage)
            if stat.tps:
                tps.labels(server_name=server.name).set(stat.tps)
                
        except ServerStatistic.DoesNotExist:
            server_online.labels(server_name=server.name).set(0)

def start_prometheus_exporter(port=9091):
    """Iniciar servidor Prometheus"""
    start_http_server(port)
    
    def update_loop():
        while True:
            update_metrics()
            time.sleep(15)  # Actualizar cada 15 segundos
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()

