import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
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
  IonItem,
  IonInput,
  IonSelect,
  IonSelectOption,
  IonToggle,
  IonButton,
  IonList,
  IonSpinner,
  IonBadge,
  IonIcon,
  IonModal,
  IonButtons,
  IonFab,
  IonFabButton,
  IonItemDivider,
  IonNote,
} from '@ionic/angular/standalone';
import { LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  serverOutline,
  cubeOutline,
  peopleOutline,
  informationCircleOutline,
  addOutline,
  addCircleOutline,
  trashOutline,
} from 'ionicons/icons';
import { ServerService } from '../../servers/services/server.service';
import { MinecraftVersionService } from '../services/minecraft-version.service';
import { UserManagementService } from '../services/user-management.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Server, User } from '../../../shared/models';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.page.html',
  styleUrls: ['./settings.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
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
    IonItem,
    IonInput,
    IonSelect,
    IonSelectOption,
    IonToggle,
    IonButton,
    IonList,
    IonSpinner,
    IonBadge,
    IonIcon,
    IonModal,
    IonButtons,
    IonFab,
    IonFabButton,
    IonItemDivider,
    IonNote,
  ],
})
export class SettingsPage implements OnInit {
  activeTab: 'server' | 'versions' | 'users' | 'system' = 'server';

  // Server settings
  serverSettings: Server | null = null;
  loading = false;
  private savingSettings = false;
  additionalPorts: Array<{ port: number; protocol: 'tcp' | 'udp'; host_port: number }> = [];

  // Versions
  versions: any[] = [];
  latestVersion: any = null;

  // Users
  djangoUsers: User[] = [];
  isCreateUserModalOpen = false;
  newUser = {
    username: '',
    email: '',
    password: '',
    is_staff: false,
    is_active: true,
  };

  constructor(
    private serverService: ServerService,
    private versionService: MinecraftVersionService,
    private userManagementService: UserManagementService,
    public authService: AuthService,
    private toast: ToastService,
    private loadingController: LoadingController
  ) {
    addIcons({
      serverOutline,
      cubeOutline,
      peopleOutline,
      informationCircleOutline,
      addOutline,
      addCircleOutline,
      trashOutline,
    });
  }

  ngOnInit(): void {
    this.loadServerSettings();
    this.loadVersions();
    this.loadLatestVersion();
    if (this.authService.currentUser?.is_staff) {
      this.loadUsers();
    }
  }

  onTabChange(event: any): void {
    const value = event.detail.value;
    if (
      value === 'server' ||
      value === 'versions' ||
      value === 'users' ||
      value === 'system'
    ) {
      this.activeTab = value;
    }
  }

  // Server Settings
  loadServerSettings(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.loading = true;
    this.serverService.getServerSettings(serverId).subscribe({
      next: (settings: any) => {
        this.serverSettings = settings;
        // Cargar puertos adicionales si existen
        if (settings.additional_ports && Array.isArray(settings.additional_ports)) {
          this.additionalPorts = settings.additional_ports.map((p: any) => ({
            port: p.port || p.container_port || 0,
            protocol: (p.protocol || 'tcp').toLowerCase() as 'tcp' | 'udp',
            host_port: p.host_port || p.port || p.container_port || 0
          }));
        } else {
          this.additionalPorts = [];
        }
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar configuración');
        this.loading = false;
      },
    });
  }

  async saveServerSettings(): Promise<void> {
    console.log('saveServerSettings llamado');
    
    // Prevenir múltiples clics
    if (this.savingSettings) {
      console.log('Ya se está guardando, ignorando click');
      return;
    }
    
    if (!this.serverSettings) {
      console.error('No hay serverSettings');
      this.toast.error('No hay configuración del servidor disponible');
      return;
    }

    this.savingSettings = true;

    console.log('ServerSettings:', this.serverSettings);

    let loading: any = null;
    // Usar Promise.race para evitar que se bloquee
    try {
      console.log('Creando loading...');
      const loadingPromise = this.loadingController.create({
        message: 'Guardando configuración...',
      });
      
      // Timeout de 2 segundos para el loading
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Loading timeout')), 2000)
      );
      
      loading = await Promise.race([loadingPromise, timeoutPromise]).catch(() => null);
      
      if (loading) {
        console.log('Loading creado:', loading);
        console.log('Presentando loading...');
        await Promise.race([
          loading.present(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Present timeout')), 1000))
        ]).catch(() => {
          console.warn('Timeout al presentar loading, continuando...');
        });
        console.log('Loading presentado exitosamente');
      } else {
        console.warn('No se pudo crear loading, continuando sin él...');
      }
    } catch (loadingError) {
      console.error('Error al crear/presentar loading:', loadingError);
      // Continuar sin loading si falla
    }
    
    console.log('Continuando después del loading...');

    // Preparar datos para enviar (mapear campos del frontend a lo que espera el backend)
    const updateData: any = {
      name: this.serverSettings.name,
      host: this.serverSettings.host,
      max_players: this.serverSettings.max_players,
      motd: this.serverSettings.motd,
      difficulty: this.serverSettings.difficulty,
      pvp: this.serverSettings.pvp,
      enable_whitelist: this.serverSettings.enable_whitelist,
      online_mode: this.serverSettings.online_mode,
      view_distance: this.serverSettings.view_distance,
      simulation_distance: this.serverSettings.simulation_distance,
      spawn_protection: this.serverSettings.spawn_protection,
      max_world_size: this.serverSettings.max_world_size,
      server_port: this.serverSettings.server_port,
      // Tipo de servidor y versión
      server_type: this.serverSettings.server_type,
      minecraft_version: this.serverSettings.minecraft_version,
      // Propiedades adicionales
      gamemode: this.serverSettings.gamemode,
      hardcore: this.serverSettings.hardcore,
      spawn_monsters: this.serverSettings.spawn_monsters,
      spawn_animals: this.serverSettings.spawn_animals,
      spawn_npcs: this.serverSettings.spawn_npcs,
      allow_flight: this.serverSettings.allow_flight,
      enable_command_block: this.serverSettings.enable_command_block,
      op_permission_level: this.serverSettings.op_permission_level,
      function_permission_level: this.serverSettings.function_permission_level,
      max_tick_time: this.serverSettings.max_tick_time,
      network_compression_threshold: this.serverSettings.network_compression_threshold,
      enforce_whitelist: this.serverSettings.enforce_whitelist,
      enforce_secure_profile: this.serverSettings.enforce_secure_profile,
      log_ips: this.serverSettings.log_ips,
      player_idle_timeout: this.serverSettings.player_idle_timeout,
      rate_limit: this.serverSettings.rate_limit,
      resource_pack: this.serverSettings.resource_pack,
      resource_pack_prompt: this.serverSettings.resource_pack_prompt,
      force_gamemode: this.serverSettings.force_gamemode,
      generate_structures: this.serverSettings.generate_structures,
      allow_nether: this.serverSettings.allow_nether,
      // Puertos adicionales
      additional_ports: this.additionalPorts
        .filter(p => p.port > 0 && p.port <= 65535)
        .map(p => ({
          port: p.port,
          protocol: p.protocol,
          host_port: p.host_port || p.port
        })),
    };

    console.log('Datos a enviar:', JSON.stringify(updateData, null, 2));
    console.log('Server ID:', this.serverSettings.id);
    console.log('Tipo de Server ID:', typeof this.serverSettings.id);

    try {
      console.log('Llamando a updateServerSettings...');
      console.log('ServerService disponible:', !!this.serverService);
      const observable = this.serverService.updateServerSettings(this.serverSettings.id, updateData);
      console.log('Observable creado:', observable);
      console.log('Tipo de Observable:', typeof observable);
      
      console.log('Suscribiendo al Observable...');
      observable.subscribe({
        next: (response: any) => {
          console.log('Respuesta recibida:', response);
          this.savingSettings = false;
          if (loading) {
            loading.dismiss();
          }
          
          // Guardar cambios pendientes de reinicio en localStorage
          if (response.requires_restart && response.requires_restart.length > 0) {
            const serverId = this.authService.currentServerId;
            if (serverId) {
              const pendingRestartKey = `pending_restart_${serverId}`;
              localStorage.setItem(pendingRestartKey, JSON.stringify(response.requires_restart));
            }
          }
          
          // Mensaje más corto
          let message = response.message || 'Configuración guardada';
          this.toast.show(message, 4000, 'success');
          
          // Recargar configuración para obtener valores actualizados
          this.loadServerSettings();
        },
        error: (error: any) => {
          console.error('Error en updateServerSettings:', error);
          console.error('Error completo:', JSON.stringify(error, null, 2));
          this.savingSettings = false;
          if (loading) {
            loading.dismiss();
          }
          const errorMsg = error.error?.error || error.message || 'Error al guardar configuración';
          this.toast.error(errorMsg);
        },
      });
    } catch (err) {
      console.error('Excepción al llamar updateServerSettings:', err);
      this.savingSettings = false;
      if (loading) {
        loading.dismiss();
      }
      this.toast.error('Error inesperado al guardar configuración');
    }
  }

  // Versions
  loadVersions(): void {
    this.versionService.getVersions().subscribe({
      next: (versions: any) => {
        this.versions = versions;
      },
      error: () => {
        // Ignorar error
      },
    });
  }

  loadLatestVersion(): void {
    this.versionService.getLatestVersion().subscribe({
      next: (version: any) => {
        this.latestVersion = version;
      },
      error: () => {
        // Ignorar error
      },
    });
  }

  // Users
  loadUsers(): void {
    if (!this.authService.currentUser?.is_staff) return;

    this.userManagementService.getUsers().subscribe({
      next: (users: any) => {
        this.djangoUsers = users;
      },
      error: () => {
        this.toast.error('Error al cargar usuarios');
      },
    });
  }

  async createUser(): Promise<void> {
    if (!this.newUser.username || !this.newUser.password) {
      this.toast.error('Usuario y contraseña son requeridos');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Creando usuario...',
    });
    await loading.present();

    this.userManagementService.createUser(this.newUser).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Usuario creado');
        this.isCreateUserModalOpen = false;
        this.resetNewUser();
        this.loadUsers();
      },
      error: () => {
        loading.dismiss();
        this.toast.error('Error al crear usuario');
      },
    });
  }

  resetNewUser(): void {
    this.newUser = {
      username: '',
      email: '',
      password: '',
      is_staff: false,
      is_active: true,
    };
  }

  addPort(): void {
    this.additionalPorts.push({
      port: 24454,
      protocol: 'udp',
      host_port: 24454
    });
  }

  removePort(index: number): void {
    this.additionalPorts.splice(index, 1);
  }
}
