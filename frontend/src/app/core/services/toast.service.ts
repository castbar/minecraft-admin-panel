import { Injectable } from '@angular/core';
import { ToastController } from '@ionic/angular/standalone';

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  constructor(private toastController: ToastController) {}

  async show(message: string, duration: number = 3000, color: 'success' | 'danger' | 'warning' | 'primary' = 'primary'): Promise<void> {
    const toast = await this.toastController.create({
      message,
      duration,
      color,
      position: 'bottom',
      buttons: [
        {
          text: 'Cerrar',
          role: 'cancel'
        }
      ]
    });
    await toast.present();
  }

  async success(message: string): Promise<void> {
    await this.show(message, 3000, 'success');
  }

  async error(message: string): Promise<void> {
    await this.show(message, 5000, 'danger');
  }

  async warning(message: string): Promise<void> {
    await this.show(message, 4000, 'warning');
  }

  async info(message: string): Promise<void> {
    await this.show(message, 3000, 'primary');
  }
}

