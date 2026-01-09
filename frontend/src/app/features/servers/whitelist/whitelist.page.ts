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
  IonAlert,
} from '@ionic/angular/standalone';
import { AlertController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  addOutline,
  removeOutline,
  searchOutline,
  checkmarkOutline,
  closeOutline,
} from 'ionicons/icons';
import { WhitelistService } from '../services/whitelist.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-whitelist',
  templateUrl: './whitelist.page.html',
  styleUrls: ['./whitelist.page.scss'],
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
    IonAlert,
  ],
})
export class WhitelistPage implements OnInit {
  whitelist: string[] = [];
  filteredWhitelist: string[] = [];
  searchTerm = '';
  loading = false;
  addingPlayer = false;
  newPlayerName = '';

  constructor(
    private whitelistService: WhitelistService,
    private authService: AuthService,
    private toast: ToastService,
    private alertController: AlertController
  ) {
    addIcons({
      addOutline,
      removeOutline,
      searchOutline,
      checkmarkOutline,
      closeOutline,
    });
  }

  ngOnInit(): void {
    this.loadWhitelist();
  }

  loadWhitelist(): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    this.loading = true;
    this.whitelistService.getWhitelist(serverId).subscribe({
      next: (response: any) => {
        const data = response.data || response || [];

        if (
          Array.isArray(data) &&
          data.length > 0 &&
          typeof data[0] === 'object'
        ) {
          this.whitelist = data.map(
            (item: any) =>
              item.name ||
              item.username ||
              item.player_name ||
              JSON.stringify(item)
          );
        } else {
          this.whitelist = data;
        }

        this.filterWhitelist();
        this.loading = false;
      },
      error: (error: any) => {
        this.toast.error('Error al cargar whitelist');
        this.loading = false;
      },
    });
  }

  filterWhitelist(): void {
    if (!this.searchTerm.trim()) {
      this.filteredWhitelist = this.whitelist;
      return;
    }

    const term = this.searchTerm.toLowerCase();
    this.filteredWhitelist = this.whitelist.filter((player) =>
      player.toLowerCase().includes(term)
    );
  }

  onSearch(event: any): void {
    this.searchTerm = event.detail.value || '';
    this.filterWhitelist();
  }

  async addPlayer(): Promise<void> {
    if (!this.newPlayerName.trim()) {
      this.toast.error('Ingresa un nombre de jugador');
      return;
    }

    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    this.addingPlayer = true;
    this.whitelistService
      .addToWhitelist(serverId, this.newPlayerName.trim())
      .subscribe({
        next: () => {
          this.toast.success(
            `Jugador ${this.newPlayerName} agregado a la whitelist`
          );
          this.newPlayerName = '';
          this.loadWhitelist();
          this.addingPlayer = false;
        },
        error: (error: any) => {
          this.toast.error(error.message || 'Error al agregar jugador');
          this.addingPlayer = false;
        },
      });
  }

  async removePlayer(playerName: string): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de eliminar a ${playerName} de la whitelist?`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel',
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: () => {
            this.doRemovePlayer(playerName);
          },
        },
      ],
    });

    await alert.present();
  }

  private doRemovePlayer(playerName: string): void {
    const serverId = this.authService.currentServerId;
    if (!serverId) {
      this.toast.error('No hay servidor seleccionado');
      return;
    }

    this.whitelistService.removeFromWhitelist(serverId, playerName).subscribe({
      next: () => {
        this.toast.success(`Jugador ${playerName} eliminado de la whitelist`);
        this.loadWhitelist();
      },
      error: (error: any) => {
        this.toast.error(error.message || 'Error al eliminar jugador');
      },
    });
  }
}
