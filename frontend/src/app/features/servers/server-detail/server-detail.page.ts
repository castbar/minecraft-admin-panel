import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import {
  IonContent,
  IonHeader,
  IonTitle,
  IonToolbar,
  IonSegment,
  IonSegmentButton,
  IonLabel,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonButton,
  IonIcon,
  IonSpinner,
  IonBadge,
  IonItem,
  IonInput,
  IonSelect,
  IonSelectOption,
  IonToggle,
  IonList,
  IonButtons
} from '@ionic/angular/standalone';
import { RouterModule as AngularRouterModule } from '@angular/router';
import { addIcons } from 'ionicons';
import { 
  playOutline, 
  stopOutline, 
  refreshOutline
} from 'ionicons/icons';
import { ServerService } from '../services/server.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Server, ServerStatus, ServerStats } from '../../../shared/models';
import { LogsViewerComponent } from '../components/logs-viewer/logs-viewer.component';
import { CommandConsoleComponent } from '../components/command-console/command-console.component';
import { ChatViewerComponent } from '../components/chat-viewer/chat-viewer.component';

@Component({
  selector: 'app-server-detail',
  templateUrl: './server-detail.page.html',
  styleUrls: ['./server-detail.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    AngularRouterModule,
    IonContent,
    IonHeader,
    IonTitle,
    IonToolbar,
    IonSegment,
    IonSegmentButton,
    IonLabel,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonButton,
    IonIcon,
    IonSpinner,
    IonBadge,
    IonItem,
    IonInput,
    IonSelect,
    IonSelectOption,
    IonToggle,
    IonList,
    IonButtons,
    LogsViewerComponent,
    CommandConsoleComponent,
    ChatViewerComponent
  ]
})
export class ServerDetailPage implements OnInit, OnDestroy {
  server: Server | null = null;
  activeTab: 'overview' | 'control' | 'logs' | 'chat' | 'config' = 'overview';
  serverStatus: ServerStatus | null = null;
  serverStats: ServerStats | null = null;
  loading = true;

  constructor(
    private route: ActivatedRoute,
    private serverService: ServerService,
    private authService: AuthService,
    private toast: ToastService
  ) {
    addIcons({
      playOutline,
      stopOutline,
      refreshOutline
    });
  }

  ngOnInit(): void {
    const serverId = this.route.snapshot.paramMap.get('id');
    if (serverId) {
      this.authService.setCurrentServerId(+serverId);
      this.loadServer(+serverId);
    }
  }

  loadServer(serverId: number): void {
    this.loading = true;
    this.serverService.getServerSettings(serverId).subscribe({
      next: (server) => {
        this.server = server;
        this.loadStatus(serverId);
        this.loadStats(serverId);
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar servidor');
        this.loading = false;
      }
    });
  }

  loadStatus(serverId: number): void {
    this.serverService.getServerStatus(serverId).subscribe({
      next: (status) => {
        this.serverStatus = status;
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  loadStats(serverId: number): void {
    this.serverService.getServerStats(serverId).subscribe({
      next: (stats) => {
        this.serverStats = stats;
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  async controlServer(action: 'start' | 'stop' | 'restart'): Promise<void> {
    if (!this.server) return;

    this.serverService.controlServer(this.server.id, action).subscribe({
      next: () => {
        this.toast.success(`Servidor ${action === 'start' ? 'iniciado' : action === 'stop' ? 'detenido' : 'reiniciado'} correctamente`);
        setTimeout(() => {
          this.loadStatus(this.server!.id);
        }, 2000);
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al controlar el servidor');
      }
    });
  }

  editServerSettings(): void {
    if (!this.server) return;
    // Redirigir a la página de configuración del servidor
    this.authService.setCurrentServerId(this.server.id);
    // Usar router si está disponible, o simplemente cambiar el tab
    this.activeTab = 'config';
  }

  onTabChange(event: any): void {
    const value = event.detail.value;
    if (value === 'overview' || value === 'control' || value === 'config' || value === 'logs' || value === 'chat') {
      this.activeTab = value as 'overview' | 'control' | 'logs' | 'chat' | 'config';
    }
  }

  ngOnDestroy(): void {
    // Cleanup si es necesario
  }
}

