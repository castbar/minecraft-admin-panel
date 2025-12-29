import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from './api.service';
import { Storage } from '@ionic/storage-angular';
import { firstValueFrom } from 'rxjs';

export interface LoginResponse {
  success: boolean;
  user?: {
    id: number;
    username: string;
    email?: string;
  };
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private isAuthenticated = false;
  private currentUser: any = null;

  constructor(
    private api: ApiService,
    private router: Router,
    private storage: Storage
  ) {
    this.checkAuth();
  }

  /**
   * Verificar si el usuario está autenticado
   */
  async checkAuth(): Promise<boolean> {
    try {
      // Intentar obtener información del usuario desde una API
      // Si falla, el usuario no está autenticado
      const response = await firstValueFrom(this.api.get('/servers/', false));
      this.isAuthenticated = response?.success || false;
      return this.isAuthenticated;
    } catch (error) {
      this.isAuthenticated = false;
      return false;
    }
  }

  /**
   * Login con usuario y contraseña
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await firstValueFrom(this.api.post<LoginResponse>(
        '/auth/login/',
        { username, password },
        false  // No incluir X-Server-ID en login
      ));

      if (response?.success) {
        this.isAuthenticated = true;
        this.currentUser = response.data;
        await this.storage.set('user', this.currentUser);
      }

      return response || { success: false, error: 'Error de autenticación' };
    } catch (error: any) {
      return {
        success: false,
        error: error.error?.error || 'Error de conexión'
      };
    }
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    try {
      await firstValueFrom(this.api.post('/auth/logout/', {}, false));
    } catch (error) {
      console.error('Error en logout:', error);
    } finally {
      this.isAuthenticated = false;
      this.currentUser = null;
      await this.storage.remove('user');
      await this.storage.remove('current_server_id');
      this.router.navigate(['/login']);
    }
  }

  /**
   * Verificar si está autenticado
   */
  getIsAuthenticated(): boolean {
    return this.isAuthenticated;
  }

  /**
   * Obtener usuario actual
   */
  getCurrentUser(): any {
    return this.currentUser;
  }
}

