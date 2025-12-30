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
  IonItem,
  IonLabel,
  IonList,
  IonBadge,
  IonSpinner,
  IonFab,
  IonFabButton,
  IonModal,
  IonInput,
  IonButtons
} from '@ionic/angular/standalone';
import { AlertController, LoadingController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { 
  addOutline,
  folderOutline,
  downloadOutline,
  refreshOutline,
  trashOutline,
  timeOutline
} from 'ionicons/icons';
import { BackupService } from '../services/backup.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { Backup } from '../../../shared/models';

@Component({
  selector: 'app-backup-list',
  templateUrl: './backup-list.page.html',
  styleUrls: ['./backup-list.page.scss'],
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
    IonModal,
    IonInput,
    IonButtons
  ]
})
export class BackupListPage implements OnInit {
  backups: Backup[] = [];
  loading = true;
  isCreateModalOpen = false;
  backupDescription = '';

  constructor(
    private backupService: BackupService,
    private authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {
    addIcons({
      addOutline,
      folderOutline,
      downloadOutline,
      refreshOutline,
      trashOutline,
      timeOutline
    });
  }

  ngOnInit(): void {
    this.loadBackups();
  }

  loadBackups(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.warning('Selecciona un servidor primero');
      this.loading = false;
      return;
    }

    this.loading = true;
    this.backupService.getBackups(serverId).subscribe({
      next: (backups) => {
        this.backups = backups.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        this.loading = false;
      },
      error: () => {
        this.toast.error('Error al cargar backups');
        this.loading = false;
      }
    });
  }

  async createBackup(): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Creando backup...'
    });
    await loading.present();

    this.backupService.createBackup(serverId, {
      description: this.backupDescription || undefined
    }).subscribe({
      next: () => {
        loading.dismiss();
        this.toast.success('Backup creado correctamente');
        this.isCreateModalOpen = false;
        this.backupDescription = '';
        this.loadBackups();
      },
      error: () => {
        loading.dismiss();
        this.toast.error('Error al crear backup');
      }
    });
  }

  async downloadBackup(backup: Backup): Promise<void> {
    const serverId = this.authService.currentServerId;
    if (!serverId) return;

    const loading = await this.loadingController.create({
      message: 'Descargando backup...'
    });
    await loading.present();

    try {
      const blob = await this.backupService.downloadBackup(serverId, backup.id).toPromise();
      if (blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${backup.filename || `backup_${backup.id}.tar.gz`}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        this.toast.success('Backup descargado');
      }
    } catch (error: any) {
      this.toast.error(error.message || 'Error al descargar backup');
    } finally {
      loading.dismiss();
    }
  }

  async deleteBackup(backup: Backup): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar el backup del ${new Date(backup.created_at).toLocaleString()}? Esta acción es irreversible.`,
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
              message: 'Eliminando backup...'
            });
            await loading.present();

            try {
              await this.backupService.deleteBackup(serverId, backup.id).toPromise();
              this.toast.success('Backup eliminado');
              this.loadBackups();
            } catch (error: any) {
              this.toast.error(error.message || 'Error al eliminar backup');
            } finally {
              loading.dismiss();
            }
          }
        }
      ]
    });

    await alert.present();
  }

  async restoreBackup(backup: Backup): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar restauración',
      message: `¿Estás seguro de restaurar el backup del ${new Date(backup.created_at).toLocaleString()}? Esto reemplazará los archivos actuales.`,
      buttons: [
        { text: 'Cancelar', role: 'cancel' },
        {
          text: 'Restaurar',
          role: 'destructive',
          handler: async () => {
            const serverId = this.authService.currentServerId;
            if (!serverId) return;

            const loading = await this.loadingController.create({
              message: 'Restaurando backup...'
            });
            await loading.present();

            this.backupService.restoreBackup(serverId, backup.id).subscribe({
              next: () => {
                loading.dismiss();
                this.toast.success('Backup restaurado correctamente');
                this.loadBackups();
              },
              error: () => {
                loading.dismiss();
                this.toast.error('Error al restaurar backup');
              }
            });
          }
        }
      ]
    });
    await alert.present();
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('es-ES');
  }

  formatBytes(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }
}
