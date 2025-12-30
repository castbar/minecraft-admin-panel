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
  IonSelect,
  IonSelectOption,
  IonSpinner,
  IonBadge,
  IonSearchbar,
  IonModal,
  IonAlert,
  IonFab,
  IonFabButton,
  IonButtons
} from '@ionic/angular/standalone';
import { AlertController, LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { 
  addOutline, 
  createOutline, 
  trashOutline,
  searchOutline,
  closeOutline,
  documentTextOutline
} from 'ionicons/icons';
import { ModTemplateService, ModTemplate } from '../services/mod-template.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-mod-templates',
  templateUrl: './mod-templates.page.html',
  styleUrls: ['./mod-templates.page.scss'],
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
    IonSelect,
    IonSelectOption,
    IonSpinner,
    IonBadge,
    IonSearchbar,
    IonModal,
    IonAlert,
    IonFab,
    IonFabButton,
    IonButtons
  ]
})
export class ModTemplatesPage implements OnInit {
  templates: ModTemplate[] = [];
  filteredTemplates: ModTemplate[] = [];
  searchTerm = '';
  loading = false;
  
  // Modal crear/editar
  isModalOpen = false;
  isEditMode = false;
  currentTemplate: ModTemplate | null = null;
  templateForm = {
    mod_name: '',
    config_file_path: '',
    default_content: '',
    file_format: 'json' as 'json' | 'yaml' | 'properties' | 'toml' | 'txt',
    description: ''
  };

  constructor(
    private modTemplateService: ModTemplateService,
    public authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      addOutline,
      createOutline,
      trashOutline,
      searchOutline,
      closeOutline,
      documentTextOutline
    });
  }

  ngOnInit(): void {
    if (!this.authService.currentUser?.is_staff) {
      this.toast.error('No tienes permisos para acceder a esta sección');
      return;
    }
    this.loadTemplates();
  }

  loadTemplates(): void {
    this.loading = true;
    this.modTemplateService.getTemplates().subscribe({
      next: (response: any) => {
        this.templates = response.data || response || [];
        this.filterTemplates();
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar plantillas');
        this.loading = false;
      }
    });
  }

  filterTemplates(): void {
    if (!this.searchTerm.trim()) {
      this.filteredTemplates = this.templates;
      return;
    }

    const term = this.searchTerm.toLowerCase();
    this.filteredTemplates = this.templates.filter(template =>
      template.mod_name.toLowerCase().includes(term) ||
      template.config_file_path.toLowerCase().includes(term) ||
      (template.description && template.description.toLowerCase().includes(term))
    );
  }

  onSearch(event: any): void {
    this.searchTerm = event.detail.value || '';
    this.filterTemplates();
  }

  openCreateModal(): void {
    this.isEditMode = false;
    this.currentTemplate = null;
    this.templateForm = {
      mod_name: '',
      config_file_path: '',
      default_content: '',
      file_format: 'json',
      description: ''
    };
    this.isModalOpen = true;
  }

  openEditModal(template: ModTemplate): void {
    this.isEditMode = true;
    this.currentTemplate = template;
    this.templateForm = {
      mod_name: template.mod_name,
      config_file_path: template.config_file_path,
      default_content: template.default_content,
      file_format: template.file_format,
      description: template.description || ''
    };
    this.isModalOpen = true;
  }

  async saveTemplate(): Promise<void> {
    if (!this.templateForm.mod_name || !this.templateForm.config_file_path || !this.templateForm.default_content) {
      this.toast.error('Completa todos los campos requeridos');
      return;
    }

    const loading = await this.loadingController.create({
      message: this.isEditMode ? 'Actualizando plantilla...' : 'Creando plantilla...'
    });
    await loading.present();

    if (this.isEditMode && this.currentTemplate) {
      this.modTemplateService.updateTemplate(this.currentTemplate.id, this.templateForm).subscribe({
        next: () => {
          loading.dismiss();
          this.toast.success('Plantilla actualizada');
          this.isModalOpen = false;
          this.loadTemplates();
        },
        error: (error: any) => {
          loading.dismiss();
          this.toast.error(error.message || 'Error al actualizar plantilla');
        }
      });
    } else {
      this.modTemplateService.createTemplate(this.templateForm).subscribe({
        next: () => {
          loading.dismiss();
          this.toast.success('Plantilla creada');
          this.isModalOpen = false;
          this.resetForm();
          this.loadTemplates();
        },
        error: (error: any) => {
          loading.dismiss();
          this.toast.error(error.message || 'Error al crear plantilla');
        }
      });
    }
  }

  async deleteTemplate(template: ModTemplate): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar la plantilla para ${template.mod_name}?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: () => {
            // Nota: No hay endpoint DELETE, solo se puede editar
            this.toast.error('La eliminación de plantillas no está disponible');
          }
        }
      ]
    });

    await alert.present();
  }

  resetForm(): void {
    this.templateForm = {
      mod_name: '',
      config_file_path: '',
      default_content: '',
      file_format: 'json',
      description: ''
    };
  }

  getFormatLabel(format: string): string {
    const labels: { [key: string]: string } = {
      'json': 'JSON',
      'yaml': 'YAML',
      'properties': 'Properties',
      'toml': 'TOML',
      'txt': 'Texto'
    };
    return labels[format] || format;
  }
}

