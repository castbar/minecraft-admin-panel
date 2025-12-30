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
  onlinePlayers: string[] = [];
  playerCount = 0;
  maxPlayers = 20;
  loading = true;
  searchTerm = '';
  isCreateModalOpen = false;
  isEditModalOpen = false;
  selectedUser: MinecraftUser | null = null;
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
    this.loadUsers();
    this.loadWhitelist();
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

  loadUsers(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.warning('Selecciona un servidor primero');
      this.loading = false;
      return;
    }

    this.loading = true;
    this.userService.getUsers(serverId).subscribe({
      next: (users) => {
        this.users = users;
        this.filteredUsers = users;
        this.loading = false;
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
        this.whitelist = response.data || response || [];
      },
      error: () => {
        // Ignorar error
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
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al agregar a whitelist');
      }
    });
  }

  private removeFromWhitelist(username: string): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.whitelistService.removeFromWhitelist(serverId, username).subscribe({
      next: () => {
        this.toast.success(`${username} eliminado de la whitelist`);
        this.loadWhitelist();
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al quitar de whitelist');
      }
    });
  }
}
