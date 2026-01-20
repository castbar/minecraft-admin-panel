import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
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
  IonBadge,
  IonSpinner,
  IonFab,
  IonFabButton,
  IonFabList,
  IonItem,
  IonLabel,
  IonList,
  IonSearchbar
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { 
  addOutline,
  serverOutline,
  playOutline,
  stopOutline,
  settingsOutline,
  eyeOutline,
  trashOutline,
  star,
  globeOutline,
  pricetagOutline,
  personOutline,
  cubeOutline,
  hardwareChipOutline,
  timeOutline
} from 'ionicons/icons';
import { ServerService } from '../services/server.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Server } from '../../../shared/models';

@Component({
  selector: 'app-server-list',
  templateUrl: './server-list.page.html',
  styleUrls: ['./server-list.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
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
    IonBadge,
    IonSpinner,
    IonFab,
    IonFabButton,
    IonFabList,
    IonItem,
    IonLabel,
    IonList,
    IonSearchbar
  ]
})
export class ServerListPage implements OnInit {
  servers: Server[] = [];
  filteredServers: Server[] = [];
  loading = true;
  searchTerm = '';
  serverStatuses: { [serverId: number]: any } = {};

  constructor(
    private serverService: ServerService,
    private authService: AuthService,
    private toast: ToastService,
    private router: Router
  ) {
    addIcons({
      addOutline,
      serverOutline,
      playOutline,
      stopOutline,
      settingsOutline,
      eyeOutline,
      trashOutline,
      star,
      globeOutline,
      pricetagOutline,
      personOutline,
      cubeOutline,
      hardwareChipOutline,
      timeOutline
    });
  }

  ngOnInit(): void {
    this.loadServers();
  }

  loadServers(): void {
    this.loading = true;
    this.serverService.getServers().subscribe({
      next: (servers) => {
        this.servers = servers;
        this.filteredServers = servers;
        this.loading = false;
        // Cargar estados de los servidores
        this.loadServerStatuses();
      },
      error: (error) => {
        this.toast.error('Error al cargar servidores');
        this.loading = false;
      }
    });
  }

  loadServerStatuses(): void {
    // Cargar estado de cada servidor
    this.servers.forEach(server => {
      this.serverService.getServerStatus(server.id).subscribe({
        next: (status) => {
          this.serverStatuses[server.id] = status;
        },
        error: () => {
          // Si falla, marcar como offline
          this.serverStatuses[server.id] = { is_running: false };
        }
      });
    });
  }

  onSearch(event: any): void {
    this.searchTerm = event.detail.value || '';
    this.filterServers();
  }

  filterServers(): void {
    if (!this.searchTerm.trim()) {
      this.filteredServers = this.servers;
      return;
    }

    const term = this.searchTerm.toLowerCase();
    this.filteredServers = this.servers.filter(server =>
      server.name.toLowerCase().includes(term) ||
      server.host.toLowerCase().includes(term) ||
      (server.role && server.role.toLowerCase().includes(term)) ||
      (server.server_type && server.server_type.toLowerCase().includes(term))
    );
  }

  selectServer(server: Server): void {
    this.authService.setCurrentServerId(server.id);
    this.router.navigate(['/dashboard']);
  }

  viewServer(server: Server): void {
    this.authService.setCurrentServerId(server.id);
    this.router.navigate(['/servers', server.id]);
  }

  getServerTypeLabel(type?: string): string {
    if (!type) return 'N/A';
    const labels: { [key: string]: string } = {
      'vanilla': 'Vanilla',
      'fabric': 'Fabric',
      'forge': 'Forge',
      'bukkit': 'Bukkit',
      'spigot': 'Spigot',
      'paper': 'Paper'
    };
    return labels[type] || type;
  }

  getServerTypeColor(type?: string): string {
    if (!type) return 'medium';
    const colors: { [key: string]: string } = {
      'vanilla': 'primary',
      'fabric': 'tertiary',
      'forge': 'warning',
      'bukkit': 'success',
      'spigot': 'success',
      'paper': 'success'
    };
    return colors[type] || 'medium';
  }

  getRoleLabel(role?: string): string {
    if (!role) return 'N/A';
    const labels: { [key: string]: string } = {
      'admin': 'Administrador',
      'moderator': 'Moderador',
      'viewer': 'Visualizador'
    };
    return labels[role] || role;
  }

  getRoleColor(role?: string): string {
    if (!role) return 'medium';
    const colors: { [key: string]: string } = {
      'admin': 'danger',
      'moderator': 'warning',
      'viewer': 'success'
    };
    return colors[role] || 'medium';
  }

  formatDate(dateString?: string): string {
    if (!dateString) return 'Nunca';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      if (days > 0) return `Hace ${days} día${days > 1 ? 's' : ''}`;
      if (hours > 0) return `Hace ${hours} hora${hours > 1 ? 's' : ''}`;
      if (minutes > 0) return `Hace ${minutes} minuto${minutes > 1 ? 's' : ''}`;
      return 'Hace unos momentos';
    } catch {
      return 'N/A';
    }
  }

  deleteServer(server: Server, event: Event): void {
    event.stopPropagation();
    
    if (!confirm(`¿Estás seguro de eliminar el servidor "${server.name}"?`)) {
      return;
    }

    this.serverService.deleteServer(server.id).subscribe({
      next: () => {
        this.toast.success('Servidor eliminado correctamente');
        this.loadServers();
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al eliminar servidor');
      }
    });
  }

  createServer(): void {
    this.router.navigate(['/servers/create']);
  }
}
