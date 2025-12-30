import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
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
  IonBadge,
  IonSpinner,
  IonFab,
  IonFabButton,
  IonSearchbar,
  IonModal,
  IonInput,
  IonToggle,
  IonSelect,
  IonSelectOption,
  IonButtons
} from '@ionic/angular/standalone';
import { AlertController, LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { 
  addOutline,
  createOutline,
  trashOutline,
  personOutline,
  mailOutline,
  shieldCheckmarkOutline,
  searchOutline,
  checkmarkCircleOutline,
  removeCircleOutline,
  radioButtonOnOutline
} from 'ionicons/icons';
import { MinecraftUserService } from '../services/minecraft-user.service';
import { WhitelistService } from '../../servers/services/whitelist.service';
import { PlayersOnlineService } from '../../servers/services/players-online.service';
import { ServerService } from '../../servers/services/server.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { MinecraftUser } from '../../../shared/models';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-player-list',
  templateUrl: './player-list.page.html',
  styleUrls: ['./player-list.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
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
    IonBadge,
    IonSpinner,
    IonFab,
    IonFabButton,
    IonSearchbar,
    IonModal,
    IonInput,
    IonToggle,
    IonSelect,
    IonSelectOption,
    IonButtons
  ]
})
export class PlayerListPage implements OnInit, OnDestroy {
  users: MinecraftUser[] = [];
  filteredUsers: MinecraftUser[] = [];
  whitelist: string[] = [];
  whitelistData: Array<{name: string, uuid: string}> = [];
  onlinePlayers: string[] = [];
  playerCount = 0;
  maxPlayers = 20;
  loading = true;
  searchTerm = '';
  isCreateModalOpen = false;
  isEditModalOpen = false;
  isAddWhitelistModalOpen = false;
  selectedUser: MinecraftUser | null = null;
  authMode: 'whitelist' | 'database' | 'both' | 'public' = 'whitelist';
  newWhitelistPlayer = '';
  private playersSubscription?: Subscription;

  newUser = {
    username: '',
    email: '',
    is_operator: false
  };

  editUser = {
    username: '',
    email: '',
    is_operator: false,
    is_active: true
  };

  constructor(
    private userService: MinecraftUserService,
    private whitelistService: WhitelistService,
    private playersOnlineService: PlayersOnlineService,
    private serverService: ServerService,
    private authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      addOutline,
      createOutline,
      trashOutline,
      personOutline,
      mailOutline,
      shieldCheckmarkOutline,
      searchOutline,
      checkmarkCircleOutline,
      removeCircleOutline,
      radioButtonOnOutline
    });
  }

  ngOnInit(): void {
    this.loadServerSettings();
    this.loadOnlinePlayers();
    // Actualizar jugadores online cada 5 segundos
    this.playersSubscription = interval(5000).subscribe(() => {
      this.loadOnlinePlayers();
    });
  }

  ngOnDestroy(): void {
    if (this.playersSubscription) {
      this.playersSubscription.unsubscribe();
    }
  }

  loadServerSettings(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.warning('Selecciona un servidor primero');
      this.loading = false;
      return;
    }

    this.loading = true;
    this.serverService.getServerSettings(serverId).subscribe({
      next: (settings: any) => {
        this.authMode = settings.auth_mode || 'whitelist';
        // Cargar datos según el modo de autenticación
        if (this.authMode === 'whitelist') {
          this.loadWhitelist();
        } else if (this.authMode === 'database' || this.authMode === 'both') {
          this.loadUsers();
        } else {
          // Modo público - no hay lista
          this.loading = false;
        }
      },
      error: (error) => {
        this.toast.error('Error al cargar configuración del servidor');
        this.loading = false;
      }
    });
  }

  loadUsers(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.userService.getUsers(serverId).subscribe({
      next: (users) => {
        this.users = users;
        this.filteredUsers = users;
        this.loading = false;
        // Si es modo 'both', también cargar whitelist
        if (this.authMode === 'both') {
          this.loadWhitelist();
        }
      },
      error: (error) => {
        this.toast.error('Error al cargar usuarios');
        this.loading = false;
      }
    });
  }

  onSearch(event: any): void {
    this.searchTerm = event.detail.value || '';
    this.filterUsers();
  }

  filterUsers(): void {
    if (!this.searchTerm.trim()) {
      this.filteredUsers = this.users;
      return;
    }

    const term = this.searchTerm.toLowerCase();
    this.filteredUsers = this.users.filter(user =>
      user.username.toLowerCase().includes(term) ||
      (user.email && user.email.toLowerCase().includes(term))
    );
  }

  get displayTitle(): string {
    if (this.authMode === 'whitelist') {
      return 'Lista Blanca';
    } else if (this.authMode === 'database') {
      return 'Usuarios Registrados';
    } else if (this.authMode === 'both') {
      return 'Usuarios y Lista Blanca';
    }
    return 'Jugadores';
  }

  canCreateUser(): boolean {
    return this.authMode === 'database' || this.authMode === 'both';
  }

  canEditUser(user: MinecraftUser): boolean {
    return (this.authMode === 'database' || this.authMode === 'both') && 
           user.source !== 'whitelist';
  }

  canDeleteUser(user: MinecraftUser): boolean {
    return (this.authMode === 'database' || this.authMode === 'both') && 
           user.source !== 'whitelist';
  }

  canManageWhitelist(): boolean {
    // Remover logs excesivos - solo loggear en casos especiales
    return this.authMode === 'whitelist' || this.authMode === 'both';
  }

  openAddWhitelistModal(): void {
    this.isAddWhitelistModalOpen = true;
  }

  async addPlayerToWhitelist(): Promise<void> {
    if (!this.newWhitelistPlayer.trim()) {
      this.toast.error('Ingresa un nombre de jugador');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    const playerName = this.newWhitelistPlayer.trim();
    this.whitelistService.addToWhitelist(serverId, playerName).subscribe({
      next: () => {
        this.toast.success(`${playerName} agregado a la whitelist`);
        this.newWhitelistPlayer = '';
        this.isAddWhitelistModalOpen = false;
        this.loadWhitelist();
        // Si es modo both, recargar usuarios también
        if (this.authMode === 'both') {
          this.loadUsers();
        }
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al agregar a whitelist');
      }
    });
  }

  async createUser(): Promise<void> {
    if (!this.newUser.username.trim()) {
      this.toast.error('El nombre de usuario es requerido');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Creando usuario...'
    });
    await loading.present();

    this.userService.createUser(serverId, {
      username: this.newUser.username,
      email: this.newUser.email || '',
      is_operator: this.newUser.is_operator
    }).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Usuario creado correctamente');
        this.isCreateModalOpen = false;
        this.resetNewUser();
        this.loadUsers();
        // Recargar whitelist si es modo both
        if (this.authMode === 'both') {
          this.loadWhitelist();
        }
      },
      error: (error) => {
        loading.dismiss();
        this.toast.error('Error al crear usuario');
      }
    });
  }

  openEditModal(user: MinecraftUser): void {
    this.selectedUser = user;
    this.editUser = {
      username: user.username,
      email: user.email || '',
      is_operator: user.is_operator,
      is_active: user.is_active
    };
    this.isEditModalOpen = true;
  }

  async updateUser(): Promise<void> {
    if (!this.selectedUser) return;

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Actualizando usuario...'
    });
    await loading.present();

    this.userService.updateUser(serverId, this.selectedUser.id, {
      username: this.editUser.username,
      email: this.editUser.email || undefined,
      is_operator: this.editUser.is_operator,
      is_active: this.editUser.is_active
    }).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Usuario actualizado correctamente');
        this.isEditModalOpen = false;
        this.selectedUser = null;
        this.loadUsers();
        // Recargar whitelist si es modo both
        if (this.authMode === 'both') {
          this.loadWhitelist();
        }
      },
      error: (error) => {
        loading.dismiss();
        this.toast.error('Error al actualizar usuario');
      }
    });
  }

  async deleteUser(user: MinecraftUser): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar al usuario ${user.username}?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: () => {
            this.performDelete(user);
          }
        }
      ]
    });

    await alert.present();
  }

  async performDelete(user: MinecraftUser): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Eliminando usuario...'
    });
    await loading.present();

    this.userService.deleteUser(serverId, user.id).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Usuario eliminado correctamente');
        this.loadUsers();
      },
      error: (error) => {
        loading.dismiss();
        this.toast.error('Error al eliminar usuario');
      }
    });
  }

  resetNewUser(): void {
    this.newUser = {
      username: '',
      email: '',
      is_operator: false
    };
  }

  loadWhitelist(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.whitelistService.getWhitelist(serverId).subscribe({
      next: (response: any) => {
        const data = response.data || response || [];
        // Si es array de objetos {name, uuid}, extraer solo nombres
        if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object' && 'name' in data[0]) {
          this.whitelistData = data;
          this.whitelist = data.map((item: any) => item.name || item);
        } else {
          // Si es array de strings
          this.whitelist = data;
          this.whitelistData = data.map((name: string) => ({ name, uuid: '' }));
        }
        // Si es modo whitelist, usar whitelist como lista principal
        if (this.authMode === 'whitelist') {
          this.users = this.whitelistData.map((item, idx) => {
            const user: MinecraftUser = {
              id: idx + 1,
              username: item.name,
              email: '',
              is_active: true,
              is_operator: false,
              last_login: null,
              created_at: null,
              updated_at: null,
              source: 'whitelist'
            };
            return user;
          });
          this.filteredUsers = this.users;
          this.loading = false;
        }
      },
      error: () => {
        // Ignorar error
        if (this.authMode === 'whitelist') {
          this.loading = false;
        }
      }
    });
  }

  loadOnlinePlayers(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.playersOnlineService.getPlayersOnline(serverId).subscribe({
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

  isPlayerOnline(username: string): boolean {
    return this.onlinePlayers.includes(username);
  }

  isInWhitelist(username: string): boolean {
    return this.whitelist.includes(username);
  }

  async toggleWhitelist(user: MinecraftUser): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const isInWhitelist = this.isInWhitelist(user.username);

    if (isInWhitelist) {
      const alert = await this.alertController.create({
        header: 'Confirmar',
        message: `¿Quitar a ${user.username} de la whitelist?`,
        buttons: [
          {
            text: 'Cancelar',
            role: 'cancel'
          },
          {
            text: 'Quitar',
            role: 'destructive',
            handler: () => {
              this.removeFromWhitelist(user.username);
            }
          }
        ]
      });
      await alert.present();
    } else {
      this.addToWhitelist(user.username);
    }
  }

  private addToWhitelist(username: string): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.whitelistService.addToWhitelist(serverId, username).subscribe({
      next: () => {
        this.toast.success(`${username} agregado a la whitelist`);
        this.loadWhitelist();
        // Si es modo both, recargar usuarios también
        if (this.authMode === 'both') {
          this.loadUsers();
        }
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al agregar a whitelist');
      }
    });
  }

  async removeFromWhitelist(username: string): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar a ${username} de la whitelist?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: () => {
            this.doRemoveFromWhitelist(username);
          }
        }
      ]
    });
    await alert.present();
  }

  private doRemoveFromWhitelist(username: string): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.whitelistService.removeFromWhitelist(serverId, username).subscribe({
      next: () => {
        this.toast.success(`${username} eliminado de la whitelist`);
        if (this.authMode === 'whitelist') {
          this.loadWhitelist();
        } else {
          this.loadWhitelist();
          this.loadUsers();
        }
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al quitar de whitelist');
      }
    });
  }
}
