# Integración del Frontend Ionic con las APIs

## Resumen

Este documento describe cómo integrar el frontend Ionic con las APIs del backend Django, incluyendo el uso del header `X-Server-ID` y la autenticación por sesiones.

## Estructura Esperada del Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── services/          # Servicios para APIs
│   │   ├── pages/             # Páginas de la app
│   │   ├── components/         # Componentes reutilizables
│   │   └── app-routing.module.ts
│   └── ...
├── package.json
├── ionic.config.json
└── angular.json
```

## 1. Servicio Base para APIs

Crear un servicio base que maneje:
- Autenticación con sesiones Django
- Header `X-Server-ID` automático
- Manejo de errores
- CSRF token

### `src/app/services/api.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Storage } from '@ionic/storage-angular';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = '/api';  // Relativo al dominio actual
  private currentServerId: number | null = null;

  constructor(
    private http: HttpClient,
    private storage: Storage
  ) {
    this.init();
  }

  async init() {
    // Cargar server_id guardado
    this.currentServerId = await this.storage.get('current_server_id');
  }

  /**
   * Establecer el servidor activo
   */
  setServerId(serverId: number | null) {
    this.currentServerId = serverId;
    this.storage.set('current_server_id', serverId);
  }

  /**
   * Obtener el servidor activo
   */
  getServerId(): number | null {
    return this.currentServerId;
  }

  /**
   * Obtener headers comunes para todas las peticiones
   */
  private getHeaders(includeServerId: boolean = true): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    // Agregar X-Server-ID si está disponible y se requiere
    if (includeServerId && this.currentServerId) {
      headers = headers.set('X-Server-ID', this.currentServerId.toString());
    }

    // CSRF token se maneja automáticamente con cookies
    return headers;
  }

  /**
   * GET request
   */
  get<T>(endpoint: string, includeServerId: boolean = true): Observable<ApiResponse<T>> {
    return this.http.get<ApiResponse<T>>(
      `${this.baseUrl}${endpoint}`,
      { headers: this.getHeaders(includeServerId), withCredentials: true }
    ).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * POST request
   */
  post<T>(endpoint: string, data: any = {}, includeServerId: boolean = true): Observable<ApiResponse<T>> {
    return this.http.post<ApiResponse<T>>(
      `${this.baseUrl}${endpoint}`,
      data,
      { headers: this.getHeaders(includeServerId), withCredentials: true }
    ).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * PUT request
   */
  put<T>(endpoint: string, data: any = {}, includeServerId: boolean = true): Observable<ApiResponse<T>> {
    return this.http.put<ApiResponse<T>>(
      `${this.baseUrl}${endpoint}`,
      data,
      { headers: this.getHeaders(includeServerId), withCredentials: true }
    ).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * DELETE request
   */
  delete<T>(endpoint: string, includeServerId: boolean = true): Observable<ApiResponse<T>> {
    return this.http.delete<ApiResponse<T>>(
      `${this.baseUrl}${endpoint}`,
      { headers: this.getHeaders(includeServerId), withCredentials: true }
    ).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * POST request con FormData (para uploads)
   */
  postFormData<T>(endpoint: string, formData: FormData, includeServerId: boolean = true): Observable<ApiResponse<T>> {
    let headers = new HttpHeaders();
    
    if (includeServerId && this.currentServerId) {
      headers = headers.set('X-Server-ID', this.currentServerId.toString());
    }

    return this.http.post<ApiResponse<T>>(
      `${this.baseUrl}${endpoint}`,
      formData,
      { headers, withCredentials: true }
    ).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Manejo de errores
   */
  private handleError = (error: HttpErrorResponse) => {
    let errorMessage = 'Error desconocido';
    
    if (error.error instanceof ErrorEvent) {
      // Error del lado del cliente
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Error del lado del servidor
      if (error.error && error.error.error) {
        errorMessage = error.error.error;
      } else {
        errorMessage = `Error ${error.status}: ${error.message}`;
      }
    }
    
    return throwError(() => ({
      success: false,
      error: errorMessage,
      status: error.status
    }));
  };
}
```

## 2. Servicio de Autenticación

### `src/app/services/auth.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from './api.service';
import { Storage } from '@ionic/storage-angular';

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
      const response = await this.api.get('/servers/').toPromise();
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
      const response = await this.api.post<LoginResponse>(
        '/auth/login/',
        { username, password },
        false  // No incluir X-Server-ID en login
      ).toPromise();

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
      await this.api.post('/auth/logout/', {}, false).toPromise();
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
```

## 3. Servicio de Servidores

### `src/app/services/servers.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface Server {
  id: number;
  name: string;
  host: string;
  server_type: string;
  minecraft_version: string;
  is_active: boolean;
  role?: string;  // Rol del usuario en este servidor
}

@Injectable({
  providedIn: 'root'
})
export class ServersService {
  constructor(private api: ApiService) {}

  /**
   * Listar servidores disponibles
   */
  getServers(): Observable<Server[]> {
    return this.api.get<Server[]>('/servers/', false).pipe(
      map(response => response.data || [])
    );
  }

  /**
   * Obtener estado de un servidor
   */
  getServerStatus(serverId: number): Observable<any> {
    return this.api.get(`/servers/${serverId}/status/`).pipe(
      map(response => response.data)
    );
  }

  /**
   * Controlar servidor (start, stop, restart, pause, unpause)
   */
  controlServer(serverId: number, action: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/control/${action}/`).pipe(
      map(response => response.data)
    );
  }

  /**
   * Establecer servidor activo
   */
  setActiveServer(serverId: number) {
    this.api.setServerId(serverId);
  }

  /**
   * Obtener servidor activo
   */
  getActiveServerId(): number | null {
    return this.api.getServerId();
  }
}
```

## 4. Servicio de Mods

### `src/app/services/mods.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface Mod {
  name: string;
  enabled: boolean;
  size: number;
  size_mb: number;
  path: string;
  has_config?: boolean;
  pool_info?: {
    id: number;
    display_name: string;
    mod_type: string;
    category: string;
    config_file_path: string;
    config_format: string;
  };
}

export interface ModPool {
  id: number;
  name: string;
  display_name: string;
  mod_type: 'mod' | 'plugin';
  compatible_server_types: string[];
  description: string;
  category: string;
  has_config: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ModsService {
  constructor(private api: ApiService) {}

  /**
   * Listar mods instalados
   */
  getMods(serverId: number): Observable<Mod[]> {
    return this.api.get<Mod[]>(`/servers/${serverId}/mods/`).pipe(
      map(response => response.data || [])
    );
  }

  /**
   * Subir mod
   */
  uploadMod(serverId: number, file: File): Observable<any> {
    const formData = new FormData();
    formData.append('mod_file', file);
    
    return this.api.postFormData(`/servers/${serverId}/mods/upload/`, formData).pipe(
      map(response => response.data)
    );
  }

  /**
   * Habilitar mod
   */
  enableMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/enable/`, { mod_name: modName }).pipe(
      map(response => response.data)
    );
  }

  /**
   * Deshabilitar mod
   */
  disableMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/disable/`, { mod_name: modName }).pipe(
      map(response => response.data)
    );
  }

  /**
   * Eliminar mod
   */
  deleteMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/delete/`, { mod_name: modName }).pipe(
      map(response => response.data)
    );
  }

  /**
   * Obtener configuración de un mod
   */
  getModConfig(serverId: number, modName: string): Observable<any> {
    return this.api.get(`/servers/${serverId}/mods/config/?mod_name=${encodeURIComponent(modName)}`).pipe(
      map(response => response.data)
    );
  }

  /**
   * Actualizar configuración de un mod
   */
  updateModConfig(serverId: number, modName: string, configContent: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/config/update/`, {
      mod_name: modName,
      config_content: configContent
    }).pipe(
      map(response => response.data)
    );
  }

  /**
   * Resetear configuración de un mod
   */
  resetModConfig(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/config/reset/`, { mod_name: modName }).pipe(
      map(response => response.data)
    );
  }

  /**
   * Listar pool de mods
   */
  getModsPool(serverType?: string): Observable<ModPool[]> {
    const endpoint = serverType 
      ? `/mods/pool/?server_type=${serverType}`
      : '/mods/pool/';
    
    return this.api.get<ModPool[]>(endpoint, false).pipe(
      map(response => response.data || [])
    );
  }

  /**
   * Obtener detalles de un mod del pool
   */
  getModPoolDetail(modId: number): Observable<ModPool> {
    return this.api.get<ModPool>(`/mods/pool/${modId}/`, false).pipe(
      map(response => response.data)
    );
  }
}
```

## 5. Configuración de Módulos

### `src/app/app.module.ts` (o `app.config.ts` si usa standalone)

```typescript
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouteReuseStrategy } from '@angular/router';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { IonicModule, IonicRouteStrategy } from '@ionic/angular';
import { IonicStorageModule } from '@ionic/storage-angular';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';

// Servicios
import { ApiService } from './services/api.service';
import { AuthService } from './services/auth.service';
import { ServersService } from './services/servers.service';
import { ModsService } from './services/mods.service';

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    IonicModule.forRoot(),
    AppRoutingModule,
    HttpClientModule,
    IonicStorageModule.forRoot()
  ],
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    ApiService,
    AuthService,
    ServersService,
    ModsService
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
```

## 6. Guard de Autenticación

### `src/app/guards/auth.guard.ts`

```typescript
import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  async canActivate(): Promise<boolean> {
    const isAuthenticated = await this.authService.checkAuth();
    
    if (!isAuthenticated) {
      this.router.navigate(['/login']);
      return false;
    }
    
    return true;
  }
}
```

## 7. Uso en Componentes

### Ejemplo: Listar Mods

```typescript
import { Component, OnInit } from '@angular/core';
import { ModsService } from '../services/mods.service';
import { ServersService } from '../services/servers.service';

@Component({
  selector: 'app-mods',
  templateUrl: './mods.page.html',
  styleUrls: ['./mods.page.scss'],
})
export class ModsPage implements OnInit {
  mods: any[] = [];
  serverId: number | null = null;
  loading = false;

  constructor(
    private modsService: ModsService,
    private serversService: ServersService
  ) {}

  async ngOnInit() {
    this.serverId = this.serversService.getActiveServerId();
    if (this.serverId) {
      await this.loadMods();
    }
  }

  async loadMods() {
    if (!this.serverId) return;
    
    this.loading = true;
    try {
      this.mods = await this.modsService.getMods(this.serverId).toPromise();
    } catch (error) {
      console.error('Error cargando mods:', error);
    } finally {
      this.loading = false;
    }
  }

  async enableMod(modName: string) {
    if (!this.serverId) return;
    
    try {
      await this.modsService.enableMod(this.serverId, modName).toPromise();
      await this.loadMods();
    } catch (error) {
      console.error('Error habilitando mod:', error);
    }
  }
}
```

## 8. Configuración de CORS y Credenciales

Asegúrate de que el frontend esté configurado para enviar cookies:

### `src/app/app.component.ts` o interceptor

```typescript
import { HttpClient } from '@angular/common/http';

// En el constructor o en un interceptor
// Las peticiones deben incluir withCredentials: true
// Esto ya está configurado en ApiService
```

## 9. Variables de Entorno

### `src/environments/environment.ts`

```typescript
export const environment = {
  production: false,
  apiUrl: '/api',  // Relativo al dominio actual
};
```

## 10. Checklist de Integración

- [ ] Crear `ApiService` con manejo de `X-Server-ID`
- [ ] Crear `AuthService` para login/logout
- [ ] Crear `ServersService` para gestión de servidores
- [ ] Crear `ModsService` para gestión de mods
- [ ] Configurar `HttpClientModule` y `IonicStorageModule`
- [ ] Crear `AuthGuard` para proteger rutas
- [ ] Configurar `withCredentials: true` en todas las peticiones
- [ ] Implementar manejo de errores global
- [ ] Probar autenticación con sesiones Django
- [ ] Probar todas las APIs con header `X-Server-ID`

## Notas Importantes

1. **Header X-Server-ID**: Todas las peticiones a `/api/servers/<id>/...` deben incluir este header
2. **Autenticación**: Usar sesiones Django (cookies), no JWT
3. **CSRF**: Django maneja CSRF automáticamente con cookies
4. **CORS**: Asegurar que `CORS_ALLOW_CREDENTIALS = True` en Django
5. **Storage**: Usar `@ionic/storage-angular` para guardar `current_server_id`

