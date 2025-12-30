import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
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
import { AlertController, LoadingController, ModalController } from '@ionic/angular';
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
import { ServerService } from '../../servers/services/server.service';
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
  configFormat: 'json' | 'yaml' | 'toml' | 'properties' | 'txt' = 'json';
  isConfigModalOpen = false;
  
  loading = false;
  isUploadModalOpen = false;
  uploadFile: File | null = null;
  isUploading = false;

  constructor(
    private modService: ModService,
    private modPoolService: ModPoolService,
    private authService: AuthService,
    private serverService: ServerService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController,
    private cdr: ChangeDetectorRef
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
    if (!serverId) {
      console.warn('ModListPage.loadInstalledMods - No serverId');
      return;
    }

    this.loading = true;
    console.log('ModListPage.loadInstalledMods - serverId:', serverId);
    this.modService.getMods(serverId).subscribe({
      next: (mods) => {
        console.log('ModListPage.loadInstalledMods - Response:', mods);
        console.log('ModListPage.loadInstalledMods - Type:', typeof mods);
        console.log('ModListPage.loadInstalledMods - Is Array:', Array.isArray(mods));
        console.log('ModListPage.loadInstalledMods - Length:', mods?.length);
        this.installedMods = mods || [];
        this.filteredInstalledMods = mods || [];
        // Incluir mods que tienen config en el pool o directamente
        this.modsWithConfig = (mods || []).filter(m => {
          const hasDirectConfig = m.has_config || false;
          const hasPoolConfig = (m as any).pool_info && (m as any).pool_info.has_config;
          return hasDirectConfig || hasPoolConfig;
        });
        this.loading = false;
      },
      error: (error) => {
        console.error('ModListPage.loadInstalledMods - Error:', error);
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

    this.isUploading = true;

    this.modService.uploadMod(serverId, this.uploadFile).subscribe({
      next: () => {
        this.isUploading = false;
        this.toast.success('Mod subido correctamente');
        this.isUploadModalOpen = false;
        this.uploadFile = null;
        this.loadInstalledMods();
      },
      error: () => {
        this.isUploading = false;
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
          handler: () => {
            const serverId = this.authService.currentServerId;
            if (!serverId) return;

            this.modService.deleteMod(serverId, mod).subscribe({
              next: () => {
                this.toast.success('Mod eliminado');
                this.loadInstalledMods();
              },
              error: () => {
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
    
    // Si no hay tipo seleccionado, obtener el tipo del servidor actual
    if (!this.selectedServerType) {
      const serverId = this.authService.currentServerId;
      if (serverId) {
        // Cargar información del servidor para obtener su tipo
        this.serverService.getServerSettings(serverId).subscribe({
          next: (settings: any) => {
            if (settings && settings.server_type) {
              params.server_type = settings.server_type;
            }
            this.loadPoolModsWithParams(params);
          },
          error: () => {
            // Si falla, cargar sin filtro de tipo
            this.loadPoolModsWithParams(params);
          }
        });
        return;
      }
    }
    
    this.loadPoolModsWithParams(params);
  }
  
  private loadPoolModsWithParams(params: any): void {
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
  openConfigModal(mod: Mod): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    // Cargar configuración y abrir modal
    this.modService.getModConfig(serverId, mod.name).subscribe({
      next: (response: any) => {
        // El ApiService ya extrae el 'data', pero verificar estructura
        const config = response.data || response;
        
        if (!config) {
          this.toast.error('No se pudo cargar la configuración');
          return;
        }
        
        this.selectedModConfig = {
          mod_name: config.mod_name || mod.name,
          config_content: config.config_content || '',
          config_file_path: config.config_file_path || ''
        };
        this.configContent = config.config_content || '';
        this.configFormat = (config.config_format || 'json') as 'json' | 'yaml' | 'toml' | 'properties' | 'txt';
        
        // Forzar detección de cambios - bug conocido de Ionic en producción
        this.isConfigModalOpen = true;
        this.cdr.detectChanges();
        
        // Fallback con setTimeout para asegurar que se abra
        setTimeout(() => {
          if (!this.isConfigModalOpen) {
            this.isConfigModalOpen = true;
            this.cdr.detectChanges();
          }
        }, 100);
      },
      error: (error: any) => {
        this.toast.error(error.error?.error || 'Error al cargar configuración');
      }
    });
  }

  async saveConfig(): Promise<void> {
    if (!this.selectedModConfig) return;

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    // Validar formato antes de enviar
    const validationError = this.validateConfigFormat(this.configContent, this.configFormat);
    if (validationError) {
      this.toast.error(validationError);
      return;
    }

    this.modService.updateModConfig(serverId, this.selectedModConfig.mod_name, {
      config_content: this.configContent
    }).subscribe({
      next: () => {
        this.toast.success('Configuración guardada correctamente');
        this.isConfigModalOpen = false;
      },
      error: (error: any) => {
        this.toast.error(error.error?.error || 'Error al guardar configuración');
      }
    });
  }

  validateConfigFormat(content: string, format: string): string | null {
    if (!content.trim()) {
      return null; // Contenido vacío es válido
    }

    try {
      if (format === 'json') {
        JSON.parse(content);
      } else if (format === 'yaml' || format === 'yml') {
        // Validación básica de YAML (sintaxis de líneas clave:valor)
        const lines = content.split('\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('-') && !trimmed.includes(':') && trimmed !== '---') {
            // Validación muy básica - en producción se podría usar una librería
            if (trimmed.includes(':') && trimmed.split(':').length === 2) {
              continue; // Formato clave:valor válido
            }
          }
        }
      } else if (format === 'toml') {
        // Validación básica de TOML
        const lines = content.split('\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('[')) {
            if (!trimmed.includes('=')) {
              // No es una línea válida de TOML
              return 'Invalid TOML format: Each line should be a key=value pair or a section header [section]';
            }
          }
        }
      } else if (format === 'properties') {
        // Validación básica de Properties
        const lines = content.split('\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('!')) {
            if (!trimmed.includes('=') && !trimmed.includes(':')) {
              return 'Invalid Properties format: Each line should be a key=value or key:value pair';
            }
          }
        }
      }
      // 'txt' no necesita validación
    } catch (e: any) {
      return `Invalid ${format.toUpperCase()}: ${e.message || String(e)}`;
    }

    return null; // Válido
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

  async installFromPool(mod: ModPool): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    const alert = await this.alertController.create({
      header: 'Instalar Mod',
      message: `¿Instalar ${mod.display_name || mod.name} en el servidor?`,
      buttons: [
        { text: 'Cancelar', role: 'cancel' },
        {
          text: 'Instalar',
          handler: () => {
            this.modPoolService.installMod(serverId, mod.id).subscribe({
              next: () => {
                this.toast.success(`${mod.display_name || mod.name} instalado correctamente`);
                this.loadInstalledMods();
              },
              error: (error: any) => {
                this.toast.error(error.error?.error || 'Error al instalar mod');
              }
            });
          }
        }
      ]
    });
    await alert.present();
  }
}
