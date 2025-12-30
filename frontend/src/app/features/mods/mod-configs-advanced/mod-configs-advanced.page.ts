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
  IonTextarea,
  IonSpinner,
  IonBadge,
  IonModal,
  IonAlert,
  IonFab,
  IonFabButton,
  IonButtons,
  IonSelect,
  IonSelectOption
} from '@ionic/angular/standalone';
import { AlertController, LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { 
  addOutline, 
  createOutline, 
  trashOutline,
  checkmarkOutline,
  closeOutline,
  documentTextOutline,
  playOutline
} from 'ionicons/icons';
import { ModConfigAdvancedService, ServerModConfig } from '../services/mod-config-advanced.service';
import { ModTemplateService } from '../services/mod-template.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-mod-configs-advanced',
  templateUrl: './mod-configs-advanced.page.html',
  styleUrls: ['./mod-configs-advanced.page.scss'],
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
    IonTextarea,
    IonSpinner,
    IonBadge,
    IonModal,
    IonAlert,
    IonFab,
    IonFabButton,
    IonButtons,
    IonSelect,
    IonSelectOption
  ]
})
export class ModConfigsAdvancedPage implements OnInit {
  configs: ServerModConfig[] = [];
  templates: any[] = [];
  loading = false;
  
  // Modal crear/editar
  isModalOpen = false;
  isEditMode = false;
  currentConfig: ServerModConfig | null = null;
  configForm = {
    mod_name: '',
    config_file_path: '',
    config_content: '',
    template_id: 0
  };

  constructor(
    private modConfigService: ModConfigAdvancedService,
    private modTemplateService: ModTemplateService,
    private authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      addOutline,
      createOutline,
      trashOutline,
      checkmarkOutline,
      closeOutline,
      documentTextOutline,
      playOutline
    });
  }

  ngOnInit(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }
    this.loadConfigs();
    this.loadTemplates();
  }

  loadConfigs(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.loading = true;
    this.modConfigService.getServerConfigs(serverId).subscribe({
      next: (response: any) => {
        this.configs = response.data || response || [];
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar configuraciones');
        this.loading = false;
      }
    });
  }

  loadTemplates(): void {
    if (!this.authService.currentUser?.is_staff) return;

    this.modTemplateService.getTemplates().subscribe({
      next: (response: any) => {
        this.templates = response.data || response || [];
      },
      error: () => {
        // Ignorar error
      }
    });
  }

  openCreateModal(): void {
    this.isEditMode = false;
    this.currentConfig = null;
    this.configForm = {
      mod_name: '',
      config_file_path: '',
      config_content: '',
      template_id: 0
    };
    this.isModalOpen = true;
  }

  openEditModal(config: ServerModConfig): void {
    this.isEditMode = true;
    this.currentConfig = config;
    this.configForm = {
      mod_name: config.mod_name,
      config_file_path: config.config_file_path,
      config_content: config.config_content,
      template_id: config.template_id || 0
    };
    this.isModalOpen = true;
  }

  onTemplateSelect(templateId: number): void {
    if (!templateId) return;

    const template = this.templates.find(t => t.id === templateId);
    if (template) {
      this.configForm.mod_name = template.mod_name;
      this.configForm.config_file_path = template.config_file_path;
      this.configForm.config_content = template.default_content;
    }
  }

  async saveConfig(): Promise<void> {
    if (!this.configForm.mod_name || !this.configForm.config_file_path || !this.configForm.config_content) {
      this.toast.error('Completa todos los campos requeridos');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: this.isEditMode ? 'Actualizando configuración...' : 'Creando configuración...'
    });
    await loading.present();

    const data: any = {
      mod_name: this.configForm.mod_name,
      config_file_path: this.configForm.config_file_path,
      config_content: this.configForm.config_content
    };

    if (this.configForm.template_id > 0) {
      data.template_id = this.configForm.template_id;
    }

    if (this.isEditMode && this.currentConfig) {
      this.modConfigService.updateServerConfig(serverId, this.currentConfig.id, data).subscribe({
        next: () => {
          loading.dismiss();
          this.toast.success('Configuración actualizada');
          this.isModalOpen = false;
          this.resetForm();
          this.loadConfigs();
        },
        error: (error: any) => {
          loading.dismiss();
          this.toast.error(error.message || 'Error al actualizar configuración');
        }
      });
      return;
    } else {
      this.modConfigService.createServerConfig(serverId, data).subscribe({
        next: () => {
          loading.dismiss();
          this.toast.success('Configuración creada');
          this.isModalOpen = false;
          this.resetForm();
          this.loadConfigs();
        },
        error: (error: any) => {
          loading.dismiss();
          this.toast.error(error.message || 'Error al crear configuración');
        }
      });
    }
  }

  async applyConfig(config: ServerModConfig): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Aplicando configuración...'
    });
    await loading.present();

    this.modConfigService.applyConfig(serverId, config.id).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Configuración aplicada');
      },
      error: (error: any) => {
        loading.dismiss();
        this.toast.error(error.message || 'Error al aplicar configuración');
      }
    });
  }

  async applyAllConfigs(): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar',
      message: '¿Estás seguro de aplicar todas las configuraciones?',
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Aplicar Todas',
          handler: () => {
            this.doApplyAllConfigs();
          }
        }
      ]
    });

    await alert.present();
  }

  private doApplyAllConfigs(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.loadingController.create({
      message: 'Aplicando todas las configuraciones...'
    }).then(loading => {
      loading.present();
      this.modConfigService.applyAllConfigs(serverId).subscribe({
        next: () => {
          loading.dismiss();
          this.toast.success('Todas las configuraciones aplicadas');
        },
        error: (error: any) => {
          loading.dismiss();
          this.toast.error(error.message || 'Error al aplicar configuraciones');
        }
      });
    });
  }

  async deleteConfig(config: ServerModConfig): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar la configuración de ${config.mod_name}?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: async () => {
            const serverId = this.authService.currentServerId;
            if (!serverId) return;

            const loading = await this.loadingController.create({
              message: 'Eliminando configuración...'
            });
            await loading.present();

            try {
              await this.modConfigService.deleteServerConfig(serverId, config.id).toPromise();
              this.toast.success('Configuración eliminada');
              this.loadConfigs();
            } catch (error: any) {
              this.toast.error(error.message || 'Error al eliminar configuración');
            } finally {
              loading.dismiss();
            }
          }
        }
      ]
    });

    await alert.present();
  }

  resetForm(): void {
    this.configForm = {
      mod_name: '',
      config_file_path: '',
      config_content: '',
      template_id: 0
    };
  }
}

