import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
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
  IonItem,
  IonLabel,
  IonInput,
  IonSelect,
  IonSelectOption,
  IonToggle,
  IonButton,
  IonList
} from '@ionic/angular/standalone';
import { LoadingController } from '@ionic/angular';
import { ServerService } from '../services/server.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { CreateServerRequest } from '../services/server.service';

@Component({
  selector: 'app-server-create',
  templateUrl: './server-create.page.html',
  styleUrls: ['./server-create.page.scss'],
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
    IonItem,
    IonLabel,
    IonInput,
    IonSelect,
    IonSelectOption,
    IonToggle,
    IonButton,
    IonList
  ]
})
export class ServerCreatePage {
  serverData: CreateServerRequest = {
    name: '',
    host: '',
    port: 25565,
    rcon_port: 25575,
    rcon_password: '',
    server_type: 'vanilla',
    version: 'latest',
    max_players: 20,
    difficulty: 'normal',
    pvp_enabled: false,
    whitelist_enabled: true
  };

  constructor(
    private serverService: ServerService,
    private authService: AuthService,
    private toast: ToastService,
    private router: Router,
    private loadingController: LoadingController
  ) {}

  async createServer(): Promise<void> {
    if (!this.serverData.name || !this.serverData.host) {
      this.toast.error('Nombre y host son requeridos');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Creando servidor...'
    });
    await loading.present();

    this.serverService.createServer(this.serverData).subscribe({
      next: (response) => {
        loading.dismiss();
        this.toast.success('Servidor creado correctamente');
        this.authService.setCurrentServerId(response.data.id);
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        loading.dismiss();
        this.toast.error('Error al crear servidor');
      }
    });
  }
}

