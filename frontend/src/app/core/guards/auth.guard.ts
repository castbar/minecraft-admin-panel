import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { ApiService } from '../services/api.service';
import { firstValueFrom } from 'rxjs';

export const authGuard: CanActivateFn = async (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const api = inject(ApiService);

  // Esperar a que el estado de autenticación se cargue
  // El AuthService carga el estado en el constructor, pero puede tardar
  // Esperamos un momento para que termine de cargar
  try {
    // Verificar si ya está autenticado
    if (authService.isAuthenticated) {
      return true;
    }

    // Si no está autenticado, esperar un momento y verificar nuevamente
    // (en caso de que loadAuthState() aún esté ejecutándose)
    await new Promise(resolve => setTimeout(resolve, 100));
    
    if (authService.isAuthenticated) {
      return true;
    }

    // Si aún no está autenticado, verificar con el servidor
    try {
      const checkResponse = await firstValueFrom(api.get<any>('/auth/check/'));
      
      if (checkResponse?.authenticated && checkResponse?.user) {
        // Sesión válida en el servidor, restaurar estado
        await authService.setAuthState({
          isAuthenticated: true,
          user: checkResponse.user,
          currentServerId: null
        });
        return true;
      }
    } catch (checkError) {
      // Sesión inválida o error, continuar al login
      console.log('authGuard - Server session check failed:', checkError);
    }

    // Guardar la URL a la que intentaba acceder
    router.navigate(['/auth/login'], {
      queryParams: { returnUrl: state.url }
    });
    return false;
  } catch (error) {
    console.error('authGuard - Error:', error);
    router.navigate(['/auth/login'], {
      queryParams: { returnUrl: state.url }
    });
    return false;
  }
};

