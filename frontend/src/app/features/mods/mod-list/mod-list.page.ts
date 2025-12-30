import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  IonContent,
  IonHeader,
  IonTitle,
  IonToolbar,
  IonTabs,
  IonTabBar,
  IonTabButton,
  IonIcon,
  IonLabel,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonButton,
  IonItem,
  IonList,
  IonBadge,
  IonSpinner,
  IonFab,
  IonFabButton,
  IonSearchbar,
  IonSegment,
  IonSegmentButton,
  IonModal,
  IonTextarea,
  IonButtons
} from '@ionic/angular/standalone';
import { AlertController, LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { 
  cubeOutline,
  addOutline,
  checkmarkOutline,
  closeOutline,
  settingsOutline,
  refreshOutline,
  trashOutline,
  downloadOutline
} from 'ionicons/icons';
import { ModService } from '../services/mod.service';
import { ModPoolService } from '../services/mod-pool.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Mod, ModPool, ModConfig } from '../../../shared/models';

@Component({
  selector: 'app-mod-list',
  templateUrl: './mod-list.page.html',
  styleUrls: ['./mod-list.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonContent,
    IonHeader,
    IonTitle,
    IonToolbar,
    IonTabs,
    IonTabBar,
    IonTabButton,
    IonIcon,
    IonLabel,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonButton,
    IonItem,
    IonList,
    IonBadge,
    IonSpinner,
    IonFab,
    IonFabButton,
    IonSearchbar,
    IonSegment,
    IonSegmentButton,
    IonModal,
    IonTextarea,
    IonButtons,
    IonFab,
    IonFabButton
  ]
})
export class ModListPage implements OnInit {
  activeTab: 'installed' | 'pool' | 'configs' = 'installed';
  
  // Installed mods
  installedMods: Mod[] = [];
  filteredInstalledMods: Mod[] = [];
  installedSearchTerm = '';
  
  // Pool mods
  poolMods: ModPool[] = [];
  filteredPoolMods: ModPool[] = [];
  poolSearchTerm = '';
  categories: string[] = [];
  selectedCategory = '';
  selectedServerType = '';
  
  // Configs
  modsWithConfig: Mod[] = [];
  selectedModConfig: ModConfig | null = null;
  configContent = '';
  isConfigModalOpen = false;
  
  loading = false;
  isUploadModalOpen = false;
  uploadFile: File | null = null;

  constructor(
    private modService: ModService,
    private modPoolService: ModPoolService,
    private authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      cubeOutline,
      addOutline,
      checkmarkOutline,
      closeOutline,
      settingsOutline,
      refreshOutline,
      trashOutline,
      downloadOutline
    });
  }

  ngOnInit(): void {
    this.loadInstalledMods();
    this.loadPoolMods();
    this.loadCategories();
  }

  onTabChange(value: any): void {
    const validTabs: ('installed' | 'pool' | 'configs')[] = ['installed', 'pool', 'configs'];
    this.activeTab = validTabs.includes(value) ? value : 'installed';
  }

  // Installed Mods
  loadInstalledMods(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.loading = true;
    this.modService.getMods(serverId).subscribe({
      next: (mods) => {
        this.installedMods = mods;
        this.filteredInstalledMods = mods;
        this.modsWithConfig = mods.filter(m => m.has_config);
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar mods');
        this.loading = false;
      }
    });
  }

  onInstalledSearch(event: any): void {
    this.installedSearchTerm = event.detail.value || '';
    this.filterInstalledMods();
  }

  filterInstalledMods(): void {
    if (!this.installedSearchTerm.trim()) {
      this.filteredInstalledMods = this.installedMods;
      return;
    }
    const term = this.installedSearchTerm.toLowerCase();
    this.filteredInstalledMods = this.installedMods.filter(m =>
      m.name.toLowerCase().includes(term)
    );
  }

  async uploadMod(): Promise<void> {
    if (!this.uploadFile) {
      this.toast.error('Selecciona un archivo');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Subiendo mod...'
    });
    await loading.present();

    this.modService.uploadMod(serverId, this.uploadFile).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Mod subido correctamente');
        this.isUploadModalOpen = false;
        this.uploadFile = null;
        this.loadInstalledMods();
      },
      error: () => {
        loading.dismiss();
        this.toast.error('Error al subir mod');
      }
    });
  }

  async toggleMod(mod: Mod): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const action = mod.enabled ? 'disable' : 'enable';
    const loading = await this.loadingController.create({
      message: `${action === 'enable' ? 'Habilitando' : 'Deshabilitando'} mod...`
    });
    await loading.present();

    const serviceCall = mod.enabled
      ? this.modService.disableMod(serverId, mod.name)
      : this.modService.enableMod(serverId, mod.name);

    serviceCall.subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success(`Mod ${action === 'enable' ? 'habilitado' : 'deshabilitado'}`);
        this.loadInstalledMods();
      },
      error: () => {
        loading.dismiss();
        this.toast.error(`Error al ${action === 'enable' ? 'habilitar' : 'deshabilitar'} mod`);
      }
    });
  }

  async deleteMod(mod: Mod): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar el mod ${mod.name}?`,
      buttons: [
        { text: 'Cancelar', role: 'cancel' },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: async () => {
            const serverId = this.authService.currentServerId;
            if (!serverId) return;

            const loading = await this.loadingController.create({
              message: 'Eliminando mod...'
            });
            await loading.present();

            this.modService.deleteMod(serverId, mod.name).subscribe({
              next: () => {
                loading.dismiss();
                this.toast.success('Mod eliminado');
                this.loadInstalledMods();
              },
              error: () => {
                loading.dismiss();
                this.toast.error('Error al eliminar mod');
              }
            });
          }
        }
      ]
    });
    await alert.present();
  }

  // Pool Mods
  loadPoolMods(): void {
    this.loading = true;
    const params: any = {};
    if (this.selectedCategory) params.category = this.selectedCategory;
    if (this.selectedServerType) params.server_type = this.selectedServerType;

    this.modPoolService.getModsPool(params).subscribe({
      next: (mods) => {
        this.poolMods = mods;
        this.filteredPoolMods = mods;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar pool de mods');
        this.loading = false;
      }
    });
  }

  loadCategories(): void {
    this.modPoolService.getCategories().subscribe({
      next: (categories) => {
        this.categories = categories;
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  onPoolSearch(event: any): void {
    this.poolSearchTerm = event.detail.value || '';
    this.filterPoolMods();
  }

  filterPoolMods(): void {
    if (!this.poolSearchTerm.trim()) {
      this.filteredPoolMods = this.poolMods;
      return;
    }
    const term = this.poolSearchTerm.toLowerCase();
    this.filteredPoolMods = this.poolMods.filter(m =>
      m.name.toLowerCase().includes(term) ||
      (m.description && m.description.toLowerCase().includes(term))
    );
  }

  // Configs
  async openConfigModal(mod: Mod): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Cargando configuración...'
    });
    await loading.present();

    this.modService.getModConfig(serverId, mod.name).subscribe({
      next: (config) => {
        loading.dismiss();
        this.selectedModConfig = config;
        this.configContent = config.config_content;
        this.isConfigModalOpen = true;
      },
      error: () => {
        loading.dismiss();
        this.toast.error('Error al cargar configuración');
      }
    });
  }

  async saveConfig(): Promise<void> {
    if (!this.selectedModConfig) return;

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Guardando configuración...'
    });
    await loading.present();

    this.modService.updateModConfig(serverId, this.selectedModConfig.mod_name, {
      config_content: this.configContent
    }).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Configuración guardada');
        this.isConfigModalOpen = false;
      },
      error: () => {
        loading.dismiss();
        this.toast.error('Error al guardar configuración');
      }
    });
  }

  async resetConfig(): Promise<void> {
    if (!this.selectedModConfig) return;

    const alert = await this.alertController.create({
      header: 'Resetear configuración',
      message: '¿Estás seguro de resetear la configuración a los valores por defecto?',
      buttons: [
        { text: 'Cancelar', role: 'cancel' },
        {
          text: 'Resetear',
          role: 'destructive',
          handler: async () => {
            const serverId = this.authService.currentServerId;
            if (!serverId) return;

            const loading = await this.loadingController.create({
              message: 'Reseteando configuración...'
            });
            await loading.present();

            this.modService.resetModConfig(serverId, this.selectedModConfig!.mod_name).subscribe({
              next: () => {
                loading.dismiss();
                this.toast.success('Configuración reseteada');
                this.isConfigModalOpen = false;
                this.loadInstalledMods();
              },
              error: () => {
                loading.dismiss();
                this.toast.error('Error al resetear configuración');
              }
            });
          }
        }
      ]
    });
    await alert.present();
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file && file.name.endsWith('.jar')) {
      this.uploadFile = file;
    } else {
      this.toast.error('Solo se permiten archivos .jar');
    }
  }

  openDownload(url: string): void {
    window.open(url, '_blank');
  }
}
