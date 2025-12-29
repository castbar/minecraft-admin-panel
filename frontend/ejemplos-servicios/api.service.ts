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
    await this.storage.create();
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

