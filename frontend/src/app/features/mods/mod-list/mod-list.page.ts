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
  downloadOutline,
  documentTextOutline,
  folderOutline,
  arrowBackOutline,
  cloudUploadOutline,
  archiveOutline,
  closeCircleOutline
} from 'ionicons/icons';
import { ModService } from '../services/mod.service';
import { ModPoolService } from '../services/mod-pool.service';
import { AuthService } from '../../../core/services/auth.service';
import { ServerService } from '../../servers/services/server.service';
import { ToastService } from '../../../core/services/toast.service';
import { Mod, ModPool, ModConfig } from '../../../shared/models';

interface ConfigFile {
  name: string;
  path: string;
  size?: number;
  mod_name?: string;
  format?: string;
  relative_path?: string;
  is_dir?: boolean;
}

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
    IonButtons
  ]
})
export class ModListPage implements OnInit {
  activeTab: 'installed' | 'configs' = 'installed';
  
  // Installed mods
  installedMods: Mod[] = [];
  filteredInstalledMods: Mod[] = [];
  installedSearchTerm = '';
  
  // Configs
  modsWithConfig: Mod[] = [];
  configFiles: ConfigFile[] = [];
  selectedModConfig: ModConfig | null = null;
  selectedConfigFile: ConfigFile | null = null;
  configContent = '';
  configFormat: 'json' | 'yaml' | 'toml' | 'properties' | 'txt' = 'json';
  isConfigModalOpen = false;
  currentConfigFilePath = '/data/config'; // Ruta actual para navegación
  
  loading = false;
  isUploadModalOpen = false;
  uploadFile: File | null = null;
  uploadFiles: File[] = [];
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
      downloadOutline,
      documentTextOutline,
      folderOutline,
      arrowBackOutline,
      cloudUploadOutline,
      archiveOutline,
      closeCircleOutline
    });
  }

  ngOnInit(): void {
    this.loadInstalledMods();
  }

  onTabChange(value: any): void {
    const validTabs: ('installed' | 'configs')[] = ['installed', 'configs'];
    this.activeTab = validTabs.includes(value) ? value : 'installed';
    if (this.activeTab === 'configs') {
      this.loadConfigFiles();
    }
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
    if (this.uploadFiles.length === 0) {
      this.toast.error('Selecciona al menos un archivo');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.isUploading = true;
    let uploadedCount = 0;
    let failedCount = 0;

    // Subir archivos uno por uno
    for (let i = 0; i < this.uploadFiles.length; i++) {
      const file = this.uploadFiles[i];
      
      try {
        await new Promise<void>((resolve, reject) => {
          this.modService.uploadMod(serverId, file).subscribe({
            next: () => {
              uploadedCount++;
              resolve();
            },
            error: (error) => {
              failedCount++;
              console.error(`Error al subir ${file.name}:`, error);
              resolve(); // Continuar con el siguiente archivo
            }
          });
        });
      } catch (error) {
        failedCount++;
        console.error(`Error al subir ${file.name}:`, error);
      }
    }

    this.isUploading = false;
    
    if (uploadedCount > 0) {
      this.toast.success(`${uploadedCount} archivo(s) subido(s) correctamente${failedCount > 0 ? `, ${failedCount} fallaron` : ''}`);
    } else {
      this.toast.error('Error al subir los archivos');
    }
    
    this.isUploadModalOpen = false;
    this.clearUploadFiles();
    this.loadInstalledMods();
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

  // Config Files
  loadConfigFiles(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    this.loading = true;
    const path = this.currentConfigFilePath || '/data/config';
    this.modService.getConfigFiles(serverId, path).subscribe({
      next: (response: any) => {
        const files = response.data || response || [];
        this.configFiles = files;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.configFiles = [];
      }
    });
  }

  browseConfigFiles(): void {
    // Resetear a la ruta raíz
    this.currentConfigFilePath = '/data/config';
    this.loadConfigFiles();
  }

  navigateUp(): void {
    // Navegar hacia arriba en la jerarquía de directorios
    if (this.currentConfigFilePath && this.currentConfigFilePath !== '/data/config') {
      const parts = this.currentConfigFilePath.split('/').filter((p: string) => p);
      if (parts.length > 2) { // Mantener al menos /data/config
        parts.pop();
        this.currentConfigFilePath = '/' + parts.join('/');
      } else {
        this.currentConfigFilePath = '/data/config';
      }
      this.loadConfigFiles();
    }
  }

  openConfigFile(file: ConfigFile): void {
    // Si es un directorio, navegar dentro de él
    if (file.is_dir) {
      this.currentConfigFilePath = file.path;
      this.loadConfigFiles();
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    this.loading = true;
    this.modService.readConfigFile(serverId, file.path).subscribe({
      next: (response: any) => {
        const data = response.data || response;
        this.selectedConfigFile = file;
        this.selectedModConfig = null; // Limpiar mod config cuando abrimos un archivo directo
        this.configContent = data.content || '';
        this.configFormat = (data.format || file.format || 'txt') as 'json' | 'yaml' | 'toml' | 'properties' | 'txt';
        this.isConfigModalOpen = true;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        this.loading = false;
        const errorMsg = error.error?.error || 'Error al leer archivo';
        // Si el error indica que es un directorio, navegar dentro de él
        if (error.error?.is_directory || errorMsg.includes('is a directory')) {
          this.currentConfigFilePath = file.path;
          this.loadConfigFiles();
        } else {
          this.toast.error(errorMsg);
        }
      }
    });
  }

  formatFileSize(bytes?: number): string {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  closeConfigModal(): void {
    this.isConfigModalOpen = false;
    this.selectedModConfig = null;
    this.selectedConfigFile = null;
    this.configContent = '';
  }

  async saveConfigFile(): Promise<void> {
    if (!this.selectedConfigFile) return;

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    // Validar formato antes de guardar
    const validationError = this.validateConfigFormat(this.configContent, this.configFormat);
    if (validationError) {
      this.toast.error(validationError);
      return;
    }

    this.modService.writeConfigFile(serverId, this.selectedConfigFile.path, this.configContent).subscribe({
      next: () => {
        this.toast.success('Archivo guardado correctamente');
        this.closeConfigModal();
        this.loadConfigFiles();
      },
      error: (error: any) => {
        this.toast.error(error.error?.error || 'Error al guardar archivo');
      }
    });
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
        this.closeConfigModal();
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
        // Validación básica de TOML - más permisiva
        // TOML permite líneas vacías, comentarios, secciones, arrays multilínea, etc.
        // La validación real se hace en el backend con librerías TOML
        // Aquí solo hacemos una validación muy básica
        const lines = content.split('\n');
        let inMultilineString = false;
        let multilineDelimiter = '';
        
        for (const line of lines) {
          const trimmed = line.trim();
          
          // Ignorar líneas vacías
          if (!trimmed) continue;
          
          // Detectar inicio de strings multilínea
          if (trimmed.includes('"""') || trimmed.includes("'''")) {
            inMultilineString = !inMultilineString;
            if (inMultilineString) {
              multilineDelimiter = trimmed.includes('"""') ? '"""' : "'''";
            }
            continue;
          }
          
          // Si estamos dentro de un string multilínea, ignorar validación
          if (inMultilineString) continue;
          
          // Ignorar comentarios
          if (trimmed.startsWith('#')) continue;
          
          // Ignorar secciones [section] o [[array]]
          if (trimmed.startsWith('[') && trimmed.endsWith(']')) continue;
          
          // Ignorar arrays inline [item1, item2]
          if (trimmed.startsWith('[') && trimmed.includes(']')) continue;
          
          // Si la línea tiene '=' es probablemente válida
          // Si no tiene '=' pero tampoco es ninguna de las anteriores, podría ser parte de un array multilínea
          // En ese caso, confiamos en la validación del backend
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
                this.closeConfigModal();
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
    const files = Array.from(event.target.files || []) as File[];
    const validFiles: File[] = [];
    
    for (const file of files) {
      if (file.name.endsWith('.jar') || file.name.endsWith('.zip')) {
        validFiles.push(file);
      } else {
        this.toast.error(`El archivo ${file.name} no es válido. Solo se permiten archivos .jar o .zip`);
      }
    }
    
    if (validFiles.length > 0) {
      this.uploadFiles = [...this.uploadFiles, ...validFiles];
      // Mantener compatibilidad con uploadFile para un solo archivo
      if (validFiles.length === 1) {
        this.uploadFile = validFiles[0];
      }
    }
  }

  removeUploadFile(index: number): void {
    this.uploadFiles.splice(index, 1);
    if (this.uploadFiles.length === 0) {
      this.uploadFile = null;
    } else if (this.uploadFiles.length === 1) {
      this.uploadFile = this.uploadFiles[0];
    }
  }

  clearUploadFiles(): void {
    this.uploadFiles = [];
    this.uploadFile = null;
  }

  openDownload(url: string): void {
    window.open(url, '_blank');
  }
}
