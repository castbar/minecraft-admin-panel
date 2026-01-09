import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonContent,
  IonHeader,
  IonTitle,
  IonToolbar,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonButton,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonSpinner,
  IonBadge,
  IonGrid,
  IonRow,
  IonCol,
  IonAlert,
  IonModal,
  IonButtons,
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  playOutline,
  stopOutline,
  refreshOutline,
  serverOutline,
  peopleOutline,
  cubeOutline,
  folderOutline,
  settingsOutline,
  documentTextOutline,
  terminalOutline,
  checkmarkCircleOutline,
  chatbubblesOutline,
  warningOutline,
  closeOutline,
} from 'ionicons/icons';
import { ServerService } from '../services/server.service';
import { PlayersOnlineService } from '../services/players-online.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Server, ServerStatus, ServerStats } from '../../../shared/models';
import { LogsViewerComponent } from '../components/logs-viewer/logs-viewer.component';
import { CommandConsoleComponent } from '../components/command-console/command-console.component';
import { ChatViewerComponent } from '../components/chat-viewer/chat-viewer.component';
import { interval, Subscription, of, Observable } from 'rxjs';
import { switchMap, catchError, tap } from 'rxjs/operators';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.page.html',
  styleUrls: ['./dashboard.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    IonContent,
    IonHeader,
    IonTitle,
    IonToolbar,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonButton,
    IonIcon,
    IonItem,
    IonLabel,
    IonList,
    IonSpinner,
    IonBadge,
    IonGrid,
    IonRow,
    IonCol,
    IonModal,
    IonButtons,
    LogsViewerComponent,
    CommandConsoleComponent,
    ChatViewerComponent,
  ],
})
export class DashboardPage implements OnInit, OnDestroy {
  currentServer: Server | null = null;
  serverStatus: ServerStatus | null = null;
  serverStats: ServerStats | null = null;
  onlinePlayers: string[] = [];
  playerCount = 0;
  maxPlayers = 20;
  loading = true;
  actionLoading = false;
  pendingRestartChanges: string[] = [];
  isRestartModalOpen = false;
  private statusSubscription?: Subscription;
  private playersSubscription?: Subscription;

  constructor(
    private serverService: ServerService,
    private playersOnlineService: PlayersOnlineService,
    private authService: AuthService,
    private toast: ToastService,
    private router: Router
  ) {
    addIcons({
      playOutline,
      stopOutline,
      refreshOutline,
      serverOutline,
      peopleOutline,
      cubeOutline,
      folderOutline,
      settingsOutline,
      documentTextOutline,
      terminalOutline,
      checkmarkCircleOutline,
      chatbubblesOutline,
      warningOutline,
      closeOutline,
    });
  }

  ngOnInit(): void {
    // Escuchar cambios en el servidor seleccionado
    this.authService.authState.subscribe((state: any) => {
      const serverId = state.currentServerId;
      if (serverId && (!this.currentServer || this.currentServer.id !== serverId)) {
        this.loadDashboard();
      } else if (!serverId) {
        this.currentServer = null;
        this.loading = false;
      }
    });
    
    this.loadDashboard();
    this.loadPendingRestartChanges();
    // Actualizar estado cada 5 segundos
    this.statusSubscription = interval(5000).subscribe(() => {
      if (this.currentServer) {
        this.loadStatus();
        this.loadPlayers();
      }
    });
  }

  loadPendingRestartChanges(): void {
    const serverId = this.authService.currentServerId;
    if (serverId) {
      const pendingRestartKey = `pending_restart_${serverId}`;
      const stored = localStorage.getItem(pendingRestartKey);
      if (stored) {
        try {
          this.pendingRestartChanges = JSON.parse(stored);
        } catch {
          this.pendingRestartChanges = [];
        }
      } else {
        this.pendingRestartChanges = [];
      }
    } else {
      this.pendingRestartChanges = [];
    }
  }

  openRestartModal(): void {
    this.isRestartModalOpen = true;
  }

  closeRestartModal(): void {
    this.isRestartModalOpen = false;
  }

  clearPendingRestartChanges(): void {
    const serverId = this.authService.currentServerId;
    if (serverId) {
      const pendingRestartKey = `pending_restart_${serverId}`;
      localStorage.removeItem(pendingRestartKey);
      this.pendingRestartChanges = [];
    }
  }

  ngOnDestroy(): void {
    if (this.statusSubscription) {
      this.statusSubscription.unsubscribe();
    }
    if (this.playersSubscription) {
      this.playersSubscription.unsubscribe();
    }
  }

  loadDashboard(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.loading = false;
      return;
    }

    this.loading = true;

    // Cargar información del servidor
    this.serverService
      .getServerSettings(serverId)
      .pipe(
        switchMap((server: any) => {
          this.currentServer = server;
          this.loadPlayers();
          return this.loadStatus();
        }),
        catchError((error: any) => {
          this.loading = false;
          return of(null);
        })
      )
      .subscribe(() => {
        this.loading = false;
      });
  }

  loadStatus(): Observable<any> {
    if (!this.currentServer) return of(null);

    return this.serverService.getServerStatus(this.currentServer.id).pipe(
      switchMap((status: any) => {
        this.serverStatus = status;
        return this.serverService.getServerStats(this.currentServer!.id);
      }),
      tap((stats: any) => {
        this.serverStats = stats;
      }),
      catchError((error: any) => {
        return of(null);
      })
    );
  }

  loadPlayers(): void {
    if (!this.currentServer) return;

    this.playersOnlineService
      .getPlayersOnline(this.currentServer.id)
      .subscribe({
        next: (response: any) => {
          const data = response.data || response;
          this.onlinePlayers = data.players || [];
          this.playerCount = data.player_count || 0;
          this.maxPlayers = data.max_players || 20;
        },
        error: () => {
          // Ignorar error
        },
      });
  }

  async controlServer(action: 'start' | 'stop' | 'restart'): Promise<void> {
    if (!this.currentServer) return;

    this.actionLoading = true;
    try {
      await this.serverService
        .controlServer(this.currentServer.id, action)
        .toPromise();
      this.toast.success(
        `Servidor ${
          action === 'start'
            ? 'iniciado'
            : action === 'stop'
            ? 'detenido'
            : 'reiniciado'
        } correctamente`
      );
      
      // Si se reinició, limpiar cambios pendientes
      if (action === 'restart') {
        this.clearPendingRestartChanges();
      }
      
      // Recargar estado después de un momento
      setTimeout(() => {
        this.loadStatus();
        this.loadPendingRestartChanges();
      }, 2000);
    } catch (error: any) {
      this.toast.error(error.message || 'Error al controlar el servidor');
    } finally {
      this.actionLoading = false;
    }
  }

  formatUptime(seconds?: number): string {
    if (!seconds) return 'N/A';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }

  formatBytes(bytes?: number): string {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024)
      return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }

  getChangeDisplayName(change: string): string {
    const displayNames: { [key: string]: string } = {
      'view_distance': 'Distancia de Vista',
      'simulation_distance': 'Distancia de Simulación',
      'max_players': 'Máximo de Jugadores',
      'motd': 'MOTD',
      'online_mode': 'Modo Online',
      'spawn_protection': 'Protección de Spawn',
      'max_world_size': 'Tamaño Máximo del Mundo',
      'server_port': 'Puerto del Servidor',
      'gamemode': 'Modo de Juego',
      'hardcore': 'Modo Hardcore',
      'spawn_monsters': 'Generar Monstruos',
      'spawn_animals': 'Generar Animales',
      'spawn_npcs': 'Generar NPCs',
      'allow_flight': 'Permitir Vuelo',
      'enable_command_block': 'Bloques de Comando',
      'op_permission_level': 'Nivel de Permisos de OP',
      'function_permission_level': 'Nivel de Permisos de Funciones',
      'max_tick_time': 'Tiempo Máximo de Tick',
      'network_compression_threshold': 'Umbral de Compresión de Red',
      'enforce_whitelist': 'Forzar Whitelist',
      'enforce_secure_profile': 'Forzar Perfil Seguro',
      'log_ips': 'Registrar IPs',
      'player_idle_timeout': 'Timeout de Inactividad',
      'rate_limit': 'Límite de Tasa',
      'resource_pack': 'Paquete de Recursos',
      'resource_pack_prompt': 'Mensaje del Paquete de Recursos',
      'force_gamemode': 'Forzar Modo de Juego',
      'generate_structures': 'Generar Estructuras',
      'allow_nether': 'Permitir Nether',
      'server_type': 'Tipo de Servidor',
      'minecraft_version': 'Versión de Minecraft',
    };
    return displayNames[change] || change.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
}
