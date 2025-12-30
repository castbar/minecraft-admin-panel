import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
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
  IonCol
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
  checkmarkCircleOutline
} from 'ionicons/icons';
import { ServerService } from '../services/server.service';
import { PlayersOnlineService } from '../services/players-online.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Server, ServerStatus, ServerStats } from '../../../shared/models';
import { LogsViewerComponent } from '../components/logs-viewer/logs-viewer.component';
import { CommandConsoleComponent } from '../components/command-console/command-console.component';
import { interval, Subscription } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';

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
    LogsViewerComponent,
    CommandConsoleComponent
  ]
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
  private statusSubscription?: Subscription;
  private playersSubscription?: Subscription;

  constructor(
    private serverService: ServerService,
    private playersOnlineService: PlayersOnlineService,
    private authService: AuthService,
    private toast: ToastService
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
      checkmarkCircleOutline
    });
  }

  ngOnInit(): void {
    this.loadDashboard();
    // Actualizar estado cada 5 segundos
    this.statusSubscription = interval(5000).subscribe(() => {
      if (this.currentServer) {
        this.loadStatus();
        this.loadPlayers();
      }
    });
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
    this.serverService.getServerSettings(serverId).pipe(
      switchMap(server => {
        this.currentServer = server;
        this.loadPlayers();
        return this.loadStatus();
      }),
      catchError(error => {
        this.toast.error('Error al cargar información del servidor');
        this.loading = false;
        return of(null);
      })
    ).subscribe(() => {
      this.loading = false;
    });
  }

  loadStatus(): any {
    if (!this.currentServer) return of(null);
    
    return this.serverService.getServerStatus(this.currentServer.id).pipe(
      switchMap(status => {
        this.serverStatus = status;
        return this.serverService.getServerStats(this.currentServer!.id);
      }),
      catchError(error => {
        return of(null);
      })
    ).subscribe(stats => {
      this.serverStats = stats;
    });
  }

  loadPlayers(): void {
    if (!this.currentServer) return;
    
    this.playersOnlineService.getPlayersOnline(this.currentServer.id).subscribe({
      next: (response: any) => {
        const data = response.data || response;
        this.onlinePlayers = data.players || [];
        this.playerCount = data.player_count || 0;
        this.maxPlayers = data.max_players || 20;
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  async controlServer(action: 'start' | 'stop' | 'restart'): Promise<void> {
    if (!this.currentServer) return;

    this.actionLoading = true;
    try {
      await this.serverService.controlServer(this.currentServer.id, action).toPromise();
      this.toast.success(`Servidor ${action === 'start' ? 'iniciado' : action === 'stop' ? 'detenido' : 'reiniciado'} correctamente`);
      // Recargar estado después de un momento
      setTimeout(() => {
        this.loadStatus();
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
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }
}
