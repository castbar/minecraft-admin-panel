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
  IonFabButton
} from '@ionic/angular/standalone';
import { LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { 
  serverOutline,
  cubeOutline,
  peopleOutline,
  informationCircleOutline,
  addOutline
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
    IonFabButton
  ]
})
export class SettingsPage implements OnInit {
  activeTab: 'server' | 'versions' | 'users' | 'system' = 'server';
  
  // Server settings
  serverSettings: Server | null = null;
  loading = false;
  
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
    is_active: true
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
      addOutline
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
    if (value === 'server' || value === 'versions' || value === 'users' || value === 'system') {
      this.activeTab = value;
    }
  }

  // Server Settings
  loadServerSettings(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.loading = true;
    this.serverService.getServerSettings(serverId).subscribe({
      next: (settings) => {
        this.serverSettings = settings;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar configuración');
        this.loading = false;
      }
    });
  }

  async saveServerSettings(): Promise<void> {
    if (!this.serverSettings) return;

    const loading = await this.loadingController.create({
      message: 'Guardando configuración...'
    });
    await loading.present();

    this.serverService.updateServerSettings(this.serverSettings.id, this.serverSettings).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Configuración guardada');
      },
      error: () => {
        loading.dismiss();
        this.toast.error('Error al guardar configuración');
      }
    });
  }

  // Versions
  loadVersions(): void {
    this.versionService.getVersions().subscribe({
      next: (versions) => {
        this.versions = versions;
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  loadLatestVersion(): void {
    this.versionService.getLatestVersion().subscribe({
      next: (version) => {
        this.latestVersion = version;
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  // Users
  loadUsers(): void {
    if (!this.authService.currentUser?.is_staff) return;

    this.userManagementService.getUsers().subscribe({
      next: (users) => {
        this.djangoUsers = users;
      },
      error: () => {
        this.toast.error('Error al cargar usuarios');
      }
    });
  }

  async createUser(): Promise<void> {
    if (!this.newUser.username || !this.newUser.password) {
      this.toast.error('Usuario y contraseña son requeridos');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Creando usuario...'
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
      }
    });
  }

  resetNewUser(): void {
    this.newUser = {
      username: '',
      email: '',
      password: '',
      is_staff: false,
      is_active: true
    };
  }
}
