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
  IonInput,
  IonSpinner,
  IonBadge,
  IonSearchbar,
  IonModal,
  IonToggle,
  IonAlert,
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
  lockClosedOutline,
  searchOutline,
  closeOutline,
  checkmarkOutline
} from 'ionicons/icons';
import { UserManagementService, ServerRole } from '../services/user-management.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { User } from '../../../shared/models';

@Component({
  selector: 'app-user-management',
  templateUrl: './user-management.page.html',
  styleUrls: ['./user-management.page.scss'],
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
    IonInput,
    IonSpinner,
    IonBadge,
  IonSearchbar,
  IonModal,
  IonToggle,
  IonAlert,
  IonButtons,
  IonFab,
  IonFabButton
  ]
})
export class UserManagementPage implements OnInit {
  users: User[] = [];
  filteredUsers: User[] = [];
  searchTerm = '';
  loading = false;
  
  // Modal crear/editar
  isModalOpen = false;
  isEditMode = false;
  currentUser: User | null = null;
  userForm = {
    username: '',
    email: '',
    password: '',
    is_staff: false,
    is_active: true
  };

  // Modal cambiar password
  isPasswordModalOpen = false;
  passwordForm = {
    new_password: '',
    confirm_password: ''
  };

  constructor(
    private userManagementService: UserManagementService,
    public authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      addOutline,
      createOutline,
      trashOutline,
      lockClosedOutline,
      searchOutline,
      closeOutline,
      checkmarkOutline
    });
  }

  ngOnInit(): void {
    if (!this.authService.currentUser?.is_staff) {
      this.toast.error('No tienes permisos para acceder a esta sección');
      return;
    }
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading = true;
    this.userManagementService.getUsers().subscribe({
      next: (users) => {
        this.users = users;
        this.filterUsers();
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar usuarios');
        this.loading = false;
      }
    });
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

  onSearch(event: any): void {
    this.searchTerm = event.detail.value || '';
    this.filterUsers();
  }

  openCreateModal(): void {
    this.isEditMode = false;
    this.currentUser = null;
    this.userForm = {
      username: '',
      email: '',
      password: '',
      is_staff: false,
      is_active: true
    };
    this.isModalOpen = true;
  }

  openEditModal(user: User): void {
    this.isEditMode = true;
    this.currentUser = user;
    this.userForm = {
      username: user.username,
      email: user.email || '',
      password: '',
      is_staff: user.is_staff || false,
      is_active: user.is_active !== false
    };
    this.isModalOpen = true;
  }

  async saveUser(): Promise<void> {
    if (!this.userForm.username) {
      this.toast.error('El nombre de usuario es requerido');
      return;
    }

    if (!this.isEditMode && !this.userForm.password) {
      this.toast.error('La contraseña es requerida para nuevos usuarios');
      return;
    }

    const loading = await this.loadingController.create({
      message: this.isEditMode ? 'Actualizando usuario...' : 'Creando usuario...'
    });
    await loading.present();

    if (this.isEditMode && this.currentUser) {
      const updateData: any = {
        email: this.userForm.email,
        is_staff: this.userForm.is_staff,
        is_active: this.userForm.is_active
      };
      
      this.userManagementService.updateUser(this.currentUser.id, updateData).subscribe({
        next: () => {
          loading.dismiss();
          this.toast.success('Usuario actualizado');
          this.isModalOpen = false;
          this.loadUsers();
        },
        error: (error: any) => {
          loading.dismiss();
          this.toast.error(error.message || 'Error al actualizar usuario');
        }
      });
    } else {
      this.userManagementService.createUser(this.userForm).subscribe({
        next: () => {
          loading.dismiss();
          this.toast.success('Usuario creado');
          this.isModalOpen = false;
          this.resetForm();
          this.loadUsers();
        },
        error: (error: any) => {
          loading.dismiss();
          this.toast.error(error.message || 'Error al crear usuario');
        }
      });
    }
  }

  async deleteUser(user: User): Promise<void> {
    if (user.id === this.authService.currentUser?.id) {
      this.toast.error('No puedes eliminar tu propio usuario');
      return;
    }

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
            this.doDeleteUser(user);
          }
        }
      ]
    });

    await alert.present();
  }

  private doDeleteUser(user: User): void {
    this.userManagementService.deleteUser(user.id).subscribe({
      next: () => {
        this.toast.success('Usuario eliminado');
        this.loadUsers();
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al eliminar usuario');
      }
    });
  }

  openPasswordModal(user: User): void {
    this.currentUser = user;
    this.passwordForm = {
      new_password: '',
      confirm_password: ''
    };
    this.isPasswordModalOpen = true;
  }

  async changePassword(): Promise<void> {
    if (!this.passwordForm.new_password) {
      this.toast.error('La nueva contraseña es requerida');
      return;
    }

    if (this.passwordForm.new_password !== this.passwordForm.confirm_password) {
      this.toast.error('Las contraseñas no coinciden');
      return;
    }

    if (!this.currentUser) return;

    const loading = await this.loadingController.create({
      message: 'Cambiando contraseña...'
    });
    await loading.present();

    this.userManagementService.changePassword(this.currentUser.id, {
      new_password: this.passwordForm.new_password
    }).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Contraseña cambiada');
        this.isPasswordModalOpen = false;
        this.passwordForm = {
          new_password: '',
          confirm_password: ''
        };
      },
      error: (error: any) => {
        loading.dismiss();
        this.toast.error(error.message || 'Error al cambiar contraseña');
      }
    });
  }

  resetForm(): void {
    this.userForm = {
      username: '',
      email: '',
      password: '',
      is_staff: false,
      is_active: true
    };
  }
}

