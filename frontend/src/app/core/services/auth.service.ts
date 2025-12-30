import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { StorageService } from './storage.service';
import { ToastService } from './toast.service';
import { LoginRequest, LoginResponse, User, AuthState } from '../../shared/models';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly AUTH_KEY = 'auth';
  private readonly USER_KEY = 'user';
  private readonly SERVER_ID_KEY = 'current_server_id';

  private authState$ = new BehaviorSubject<AuthState>({
    isAuthenticated: false,
    user: null,
    currentServerId: null
  });

  constructor(
    private api: ApiService,
    private storage: StorageService,
    private toast: ToastService,
    private router: Router
  ) {
    this.loadAuthState();
  }

  get authState(): Observable<AuthState> {
    return this.authState$.asObservable();
  }

  get isAuthenticated(): boolean {
    return this.authState$.value.isAuthenticated;
  }

  get currentUser(): User | null {
    return this.authState$.value.user;
  }

  get currentServerId(): number | null {
    return this.authState$.value.currentServerId;
  }

  async login(credentials: LoginRequest): Promise<boolean> {
    console.log('=== AuthService.login - INICIO ===');
    try {
      console.log('AuthService.login - Credenciales recibidas:', credentials);
      console.log('AuthService.login - ApiService:', this.api);
      console.log('AuthService.login - ApiService existe?', !!this.api);
      console.log('AuthService.login - ApiService.post existe?', typeof this.api?.post);
      
      // El ApiService extrae automáticamente el campo 'data', así que la respuesta
      // ya viene como {user: ..., token: ..., servers: ...} en lugar de {success: true, data: {...}}
      console.log('AuthService.login - Creando Observable...');
      const endpoint = '/auth/login/';
      console.log('AuthService.login - Endpoint:', endpoint);
      console.log('AuthService.login - Llamando this.api.post...');
      
      const observable = this.api.post<any>(endpoint, credentials);
      console.log('AuthService.login - Observable creado:', observable);
      console.log('AuthService.login - Tipo de Observable:', typeof observable);
      console.log('AuthService.login - Observable tiene subscribe?', typeof observable?.subscribe);
      
      console.log('AuthService.login - Llamando firstValueFrom...');
      console.log('AuthService.login - firstValueFrom existe?', typeof firstValueFrom);
      
      const responseData = await firstValueFrom(observable);
      console.log('AuthService.login - Respuesta recibida:', responseData);
      console.log('AuthService.login - Tipo de respuesta:', typeof responseData);
      console.log('AuthService.login - responseData tiene user?', !!responseData?.user);
      
      // Verificar si la respuesta tiene el formato esperado
      if (responseData?.user) {
        const user = responseData.user as User;
        console.log('AuthService.login - Usuario autenticado:', user);
        console.log('AuthService.login - Guardando estado de autenticación...');
        await this.setAuthState({
          isAuthenticated: true,
          user,
          currentServerId: null
        });
        console.log('AuthService.login - Estado guardado exitosamente');
        console.log('=== AuthService.login - ÉXITO ===');
        return true;
      } else {
        const errorMsg = responseData?.error || 'Error al iniciar sesión';
        console.error('AuthService.login - Error en respuesta:', errorMsg);
        console.error('AuthService.login - Respuesta completa:', responseData);
        this.toast.error(errorMsg);
        console.log('=== AuthService.login - ERROR (respuesta inválida) ===');
        return false;
      }
    } catch (error: any) {
      console.error('=== AuthService.login - EXCEPCIÓN ===');
      console.error('AuthService.login - Error:', error);
      console.error('AuthService.login - Tipo de error:', typeof error);
      console.error('AuthService.login - Error.name:', error?.name);
      console.error('AuthService.login - Error.message:', error?.message);
      console.error('AuthService.login - Error.stack:', error?.stack);
      console.error('AuthService.login - Error completo:', JSON.stringify(error, null, 2));
      
      const errorMsg = error?.error?.error || error?.message || 'Error al iniciar sesión';
      console.error('AuthService.login - Mensaje de error a mostrar:', errorMsg);
      this.toast.error(errorMsg);
      console.log('=== AuthService.login - FIN (con error) ===');
      return false;
    }
  }

  async logout(): Promise<void> {
    try {
      await firstValueFrom(this.api.post('/auth/logout/'));
    } catch (error) {
      // Ignorar errores en logout
    } finally {
      await this.clearAuthState();
      this.router.navigate(['/auth/login']);
    }
  }

  setCurrentServerId(serverId: number | null): void {
    const currentState = this.authState$.value;
    this.authState$.next({
      ...currentState,
      currentServerId: serverId
    });
    if (serverId) {
      this.storage.set(this.SERVER_ID_KEY, serverId);
    } else {
      this.storage.remove(this.SERVER_ID_KEY);
    }
  }

  public async setAuthState(state: AuthState): Promise<void> {
    this.authState$.next(state);
    await this.storage.set(this.AUTH_KEY, state.isAuthenticated);
    if (state.user) {
      await this.storage.set(this.USER_KEY, state.user);
    }
    if (state.currentServerId) {
      await this.storage.set(this.SERVER_ID_KEY, state.currentServerId);
    }
  }

  private async clearAuthState(): Promise<void> {
    this.authState$.next({
      isAuthenticated: false,
      user: null,
      currentServerId: null
    });
    await this.storage.remove(this.AUTH_KEY);
    await this.storage.remove(this.USER_KEY);
    await this.storage.remove(this.SERVER_ID_KEY);
  }

  private async loadAuthState(): Promise<void> {
    try {
      // Primero verificar la sesión del servidor (cookie)
      // Esto es más confiable que solo el storage local
      try {
        const checkResponse = await firstValueFrom(this.api.get<any>('/auth/check/'));
        console.log('AuthService.loadAuthState - Server session check:', checkResponse);
        
        if (checkResponse?.authenticated && checkResponse?.user) {
          const user = checkResponse.user as User;
          const currentServerId = await this.storage.get<number>(this.SERVER_ID_KEY);
          
          this.authState$.next({
            isAuthenticated: true,
            user,
            currentServerId: currentServerId || null
          });
          
          // Actualizar storage local con los datos del servidor
          await this.storage.set(this.AUTH_KEY, true);
          await this.storage.set(this.USER_KEY, user);
          
          console.log('AuthService.loadAuthState - Session restored from server');
          return;
        }
      } catch (checkError: any) {
        // Si la verificación del servidor falla (401, etc.), el usuario no está autenticado
        console.log('AuthService.loadAuthState - Server session check failed:', checkError);
        // Continuar para verificar storage local como fallback
      }
      
      // Fallback: verificar storage local
      const isAuthenticated = await this.storage.get<boolean>(this.AUTH_KEY);
      const user = await this.storage.get<User>(this.USER_KEY);
      const currentServerId = await this.storage.get<number>(this.SERVER_ID_KEY);

      if (isAuthenticated && user) {
        // Verificar nuevamente con el servidor antes de confiar en el storage local
        try {
          const checkResponse = await firstValueFrom(this.api.get<any>('/auth/check/'));
          if (checkResponse?.authenticated && checkResponse?.user) {
            // Sesión del servidor válida, usar datos del servidor
            const serverUser = checkResponse.user as User;
            this.authState$.next({
              isAuthenticated: true,
              user: serverUser,
              currentServerId: currentServerId || null
            });
            await this.storage.set(this.USER_KEY, serverUser);
            console.log('AuthService.loadAuthState - Session validated with server');
          } else {
            // Sesión del servidor inválida, limpiar storage local
            await this.clearAuthState();
            console.log('AuthService.loadAuthState - Server session invalid, cleared local storage');
          }
        } catch (error) {
          // Si falla la verificación, limpiar estado local por seguridad
          await this.clearAuthState();
          console.log('AuthService.loadAuthState - Server check failed, cleared local storage');
        }
      }
    } catch (error) {
      console.error('Error loading auth state:', error);
    }
  }
}

