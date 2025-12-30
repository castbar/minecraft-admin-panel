import { Component, OnInit } from '@angular/core';
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
  IonList,
  IonItem,
  IonLabel,
  IonSelect,
  IonSelectOption,
  IonSpinner,
  IonBadge,
  IonAlert,
  IonModal,
  IonButtons,
  IonFab,
  IonFabButton
} from '@ionic/angular/standalone';
import { AlertController, LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { 
  addOutline, 
  createOutline, 
  trashOutline,
  peopleOutline,
  serverOutline
} from 'ionicons/icons';
import { UserManagementService, ServerRole, AssignRoleRequest } from '../services/user-management.service';
import { ServerService } from '../../servers/services/server.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Server, User } from '../../../shared/models';

@Component({
  selector: 'app-role-management',
  templateUrl: './role-management.page.html',
  styleUrls: ['./role-management.page.scss'],
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
    IonList,
    IonItem,
    IonLabel,
    IonSelect,
    IonSelectOption,
    IonSpinner,
    IonBadge,
    IonAlert,
    IonModal,
    IonButtons,
    IonFab,
    IonFabButton
  ]
})
export class RoleManagementPage implements OnInit {
  server: Server | null = null;
  roles: ServerRole[] = [];
  allUsers: User[] = [];
  loading = false;
  
  // Modal asignar rol
  isAssignModalOpen = false;
  assignForm = {
    user_id: 0,
    role: 'viewer' as 'admin' | 'moderator' | 'viewer'
  };

  // Modal editar rol
  isEditModalOpen = false;
  editingRole: ServerRole | null = null;
  editForm = {
    role: 'viewer' as 'admin' | 'moderator' | 'viewer'
  };

  roleLabels: { [key: string]: string } = {
    'admin': 'Administrador',
    'moderator': 'Moderador',
    'viewer': 'Visualizador'
  };

  constructor(
    private userManagementService: UserManagementService,
    private serverService: ServerService,
    public authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      addOutline,
      createOutline,
      trashOutline,
      peopleOutline,
      serverOutline
    });
  }

  ngOnInit(): void {
    this.loadServer();
    this.loadRoles();
    if (this.authService.currentUser?.is_staff) {
      this.loadAllUsers();
    }
  }

  loadServer(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    this.serverService.getServerSettings(serverId).subscribe({
      next: (server) => {
        this.server = server;
      },
      error: () => {
        this.toast.error('Error al cargar servidor');
      }
    });
  }

  loadRoles(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.loading = true;
    this.userManagementService.getServerRoles(serverId).subscribe({
      next: (response: any) => {
        this.roles = response.data || response || [];
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar roles');
        this.loading = false;
      }
    });
  }

  loadAllUsers(): void {
    if (!this.authService.currentUser?.is_staff) return;

    this.userManagementService.getUsers().subscribe({
      next: (users) => {
        this.allUsers = users;
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  openAssignModal(): void {
    this.assignForm = {
      user_id: 0,
      role: 'viewer'
    };
    this.isAssignModalOpen = true;
  }

  async assignRole(): Promise<void> {
    if (!this.assignForm.user_id) {
      this.toast.error('Selecciona un usuario');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Asignando rol...'
    });
    await loading.present();

    this.userManagementService.assignRole(serverId, {
      user_id: this.assignForm.user_id,
      role: this.assignForm.role
    }).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Rol asignado');
        this.isAssignModalOpen = false;
        this.loadRoles();
      },
      error: (error: any) => {
        loading.dismiss();
        this.toast.error(error.message || 'Error al asignar rol');
      }
    });
  }

  openEditModal(role: ServerRole): void {
    this.editingRole = role;
    this.editForm = {
      role: role.role
    };
    this.isEditModalOpen = true;
  }

  async updateRole(): Promise<void> {
    if (!this.editingRole) return;

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Actualizando rol...'
    });
    await loading.present();

    this.userManagementService.updateRole(serverId, this.editingRole.id, {
      role: this.editForm.role
    }).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Rol actualizado');
        this.isEditModalOpen = false;
        this.editingRole = null;
        this.loadRoles();
      },
      error: (error: any) => {
        loading.dismiss();
        this.toast.error(error.message || 'Error al actualizar rol');
      }
    });
  }

  async removeRole(role: ServerRole): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar el rol de ${role.user.username}?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: () => {
            this.doRemoveRole(role);
          }
        }
      ]
    });

    await alert.present();
  }

  private doRemoveRole(role: ServerRole): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.userManagementService.removeRole(serverId, role.id).subscribe({
      next: () => {
        this.toast.success('Rol eliminado');
        this.loadRoles();
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al eliminar rol');
      }
    });
  }

  getAvailableUsers(): User[] {
    const assignedUserIds = this.roles.map(r => r.user.id);
    return this.allUsers.filter(u => !assignedUserIds.includes(u.id));
  }
}

