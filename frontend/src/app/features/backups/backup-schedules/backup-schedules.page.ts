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
  IonSelect,
  IonSelectOption,
  IonToggle,
  IonSpinner,
  IonBadge,
  IonModal,
  IonDatetime,
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
  timeOutline,
  calendarOutline,
  checkmarkOutline,
  closeOutline
} from 'ionicons/icons';
import { BackupService, BackupSchedule } from '../services/backup.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-backup-schedules',
  templateUrl: './backup-schedules.page.html',
  styleUrls: ['./backup-schedules.page.scss'],
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
    IonSelect,
    IonSelectOption,
    IonToggle,
    IonSpinner,
    IonBadge,
    IonModal,
    IonDatetime,
    IonAlert,
    IonFab,
    IonFabButton,
    IonButtons
  ]
})
export class BackupSchedulesPage implements OnInit {
  schedules: BackupSchedule[] = [];
  loading = false;
  
  // Modal crear/editar
  isModalOpen = false;
  isEditMode = false;
  currentSchedule: BackupSchedule | null = null;
  scheduleForm = {
    schedule_type: 'daily' as 'daily' | 'weekly' | 'monthly',
    schedule_time: '',
    keep_count: 5,
    enabled: true
  };

  constructor(
    private backupService: BackupService,
    private authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      addOutline,
      createOutline,
      trashOutline,
      timeOutline,
      calendarOutline,
      checkmarkOutline,
      closeOutline
    });
  }

  ngOnInit(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }
    this.loadSchedules();
  }

  loadSchedules(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    this.loading = true;
    this.backupService.getBackupSchedules(serverId).subscribe({
      next: (response: any) => {
        this.schedules = response.data || response || [];
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar programaciones');
        this.loading = false;
      }
    });
  }

  openCreateModal(): void {
    this.isEditMode = false;
    this.currentSchedule = null;
    this.scheduleForm = {
      schedule_type: 'daily',
      schedule_time: new Date().toISOString().substring(0, 16),
      keep_count: 5,
      enabled: true
    };
    this.isModalOpen = true;
  }

  openEditModal(schedule: BackupSchedule): void {
    this.isEditMode = true;
    this.currentSchedule = schedule;
    this.scheduleForm = {
      schedule_type: schedule.schedule_type,
      schedule_time: schedule.schedule_time || new Date().toISOString().substring(0, 16),
      keep_count: schedule.keep_count,
      enabled: schedule.enabled
    };
    this.isModalOpen = true;
  }

  async saveSchedule(): Promise<void> {
    if (!this.scheduleForm.schedule_time) {
      this.toast.error('Selecciona una hora');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    const loading = await this.loadingController.create({
      message: this.isEditMode ? 'Actualizando programación...' : 'Creando programación...'
    });
    await loading.present();

    try {
      const data: any = {
        schedule_type: this.scheduleForm.schedule_type,
        schedule_time: this.scheduleForm.schedule_time,
        keep_count: this.scheduleForm.keep_count,
        enabled: this.scheduleForm.enabled
      };

      if (this.isEditMode && this.currentSchedule) {
        await this.backupService.updateBackupSchedule(serverId, this.currentSchedule.id, data).toPromise();
        this.toast.success('Programación actualizada');
      } else {
        await this.backupService.createBackupSchedule(serverId, data).toPromise();
        this.toast.success('Programación creada');
      }
      this.isModalOpen = false;
      this.loadSchedules();
    } catch (error: any) {
      this.toast.error(error.message || 'Error al guardar programación');
    } finally {
      loading.dismiss();
    }
  }

  async deleteSchedule(schedule: BackupSchedule): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar esta programación?`,
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
              message: 'Eliminando programación...'
            });
            await loading.present();

            try {
              await this.backupService.deleteBackupSchedule(serverId, schedule.id).toPromise();
              this.toast.success('Programación eliminada');
              this.loadSchedules();
            } catch (error: any) {
              this.toast.error(error.message || 'Error al eliminar programación');
            } finally {
              loading.dismiss();
            }
          }
        }
      ]
    });

    await alert.present();
  }

  getScheduleTypeLabel(type: string): string {
    const labels: { [key: string]: string } = {
      'daily': 'Diario',
      'weekly': 'Semanal',
      'monthly': 'Mensual'
    };
    return labels[type] || type;
  }

  formatDate(dateString?: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('es-ES');
  }
}

