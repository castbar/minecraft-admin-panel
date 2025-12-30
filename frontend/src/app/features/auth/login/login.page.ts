import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonItem,
  IonLabel,
  IonInput,
  IonButton,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent
} from '@ionic/angular/standalone';
import { LoadingController } from '@ionic/angular';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { LoginRequest } from '../../../shared/models';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonItem,
    IonLabel,
    IonInput,
    IonButton,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent
  ]
})
export class LoginPage {
  credentials: LoginRequest = {
    username: '',
    password: ''
  };

  constructor(
    private authService: AuthService,
    private router: Router,
    private toast: ToastService,
    private loadingController: LoadingController
  ) {}

  async login(): Promise<void> {
    console.log('=== LoginPage.login - INICIO ===');
    console.log('LoginPage.login - Credenciales:', this.credentials);
    console.log('LoginPage.login - authService:', this.authService);
    console.log('LoginPage.login - router:', this.router);
    console.log('LoginPage.login - loadingController:', this.loadingController);
    console.log('LoginPage.login - loadingController.create existe?', typeof this.loadingController?.create);
    
    // Validar que los campos no estén vacíos
    console.log('LoginPage.login - Validando campos...');
    if (!this.credentials.username || !this.credentials.password) {
      console.log('LoginPage.login - Campos vacíos, retornando');
      this.toast.error('Por favor completa todos los campos');
      return;
    }
    console.log('LoginPage.login - Campos válidos');

    // Omitir loading por ahora para debug
    console.log('LoginPage.login - Omitiendo loading para debug...');

    try {
      console.log('LoginPage.login - Llamando authService.login...');
      console.log('LoginPage.login - authService.login existe?', typeof this.authService.login);
      console.log('LoginPage.login - authService.login es función?', this.authService.login instanceof Function);
      
      const loginPromise = this.authService.login(this.credentials);
      console.log('LoginPage.login - Promise creada:', loginPromise);
      console.log('LoginPage.login - Promise tiene then?', typeof loginPromise?.then);
      
      console.log('LoginPage.login - Esperando respuesta...');
      const success = await loginPromise;
      console.log('LoginPage.login - Respuesta de authService:', success);
      console.log('LoginPage.login - Tipo de respuesta:', typeof success);

      if (success) {
        console.log('LoginPage.login - Login exitoso, navegando a dashboard...');
        this.router.navigate(['/dashboard']);
        console.log('LoginPage.login - Navegación iniciada');
      } else {
        console.log('LoginPage.login - Login falló (success = false)');
      }
    } catch (authError) {
      console.error('=== LoginPage.login - EXCEPCIÓN CAPTURADA ===');
      console.error('LoginPage.login - Error:', authError);
      console.error('LoginPage.login - Tipo de error:', typeof authError);
      console.error('LoginPage.login - Error.name:', authError instanceof Error ? authError.name : 'N/A');
      console.error('LoginPage.login - Error.message:', authError instanceof Error ? authError.message : 'N/A');
      console.error('LoginPage.login - Error.stack:', authError instanceof Error ? authError.stack : 'N/A');
      console.error('LoginPage.login - Error completo:', JSON.stringify(authError, Object.getOwnPropertyNames(authError), 2));
      this.toast.error('Error al iniciar sesión');
    }
    
    console.log('=== LoginPage.login - FIN ===');
  }
}

