import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../../shared/models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    });
  }

  get<T>(endpoint: string, params?: any): Observable<T> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
          httpParams = httpParams.set(key, params[key].toString());
        }
      });
    }
    return this.http.get<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, {
      headers: this.getHeaders(),
      params: httpParams,
      withCredentials: true
    }).pipe(
      map(res => (res as any).data !== undefined ? (res as any).data : res),
      catchError(this.handleError)
    );
  }

  post<T>(endpoint: string, data?: any): Observable<T> {
    console.log('=== ApiService.post - INICIO ===');
    console.log('ApiService.post - Endpoint recibido:', endpoint);
    console.log('ApiService.post - Data recibida:', data);
    console.log('ApiService.post - Base URL:', this.baseUrl);
    console.log('ApiService.post - HttpClient:', this.http);
    console.log('ApiService.post - HttpClient existe?', !!this.http);
    
    // Si es FormData, no establecer Content-Type (el navegador lo hace automáticamente)
    console.log('ApiService.post - Obteniendo headers...');
    let headers = this.getHeaders();
    console.log('ApiService.post - Headers iniciales:', headers);
    
    if (data instanceof FormData) {
      console.log('ApiService.post - Data es FormData, removiendo Content-Type');
      headers = headers.delete('Content-Type');
    }
    console.log('ApiService.post - Headers finales:', headers);
    
    const url = `${this.baseUrl}${endpoint}`;
    console.log('ApiService.post - URL completa:', url);
    console.log('ApiService.post - Configuración de request:', {
      headers: headers.keys(),
      withCredentials: true
    });
    
    console.log('ApiService.post - Llamando this.http.post...');
    const httpObservable = this.http.post<ApiResponse<T>>(url, data, {
      headers,
      withCredentials: true
    });
    console.log('ApiService.post - Observable HTTP creado:', httpObservable);
    
    console.log('ApiService.post - Aplicando pipe con map y catchError...');
    const result = httpObservable.pipe(
      map(res => {
        console.log('ApiService.post - map - Respuesta raw recibida:', res);
        console.log('ApiService.post - map - Tipo de respuesta:', typeof res);
        console.log('ApiService.post - map - Tiene data?', (res as any)?.data !== undefined);
        const mapped = (res as any).data !== undefined ? (res as any).data : res;
        console.log('ApiService.post - map - Respuesta mapeada:', mapped);
        return mapped;
      }),
      catchError(error => {
        console.error('=== ApiService.post - catchError ===');
        console.error('ApiService.post - Error capturado:', error);
        console.error('ApiService.post - Error.status:', error?.status);
        console.error('ApiService.post - Error.statusText:', error?.statusText);
        console.error('ApiService.post - Error.error:', error?.error);
        console.error('ApiService.post - Error.message:', error?.message);
        console.error('ApiService.post - Error.stack:', error?.stack);
        return this.handleError(error);
      })
    );
    
    console.log('ApiService.post - Observable final creado:', result);
    console.log('=== ApiService.post - FIN (retornando Observable) ===');
    return result;
  }

  put<T>(endpoint: string, data?: any): Observable<T> {
    return this.http.put<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data, {
      headers: this.getHeaders(),
      withCredentials: true
    }).pipe(
      map(res => (res as any).data !== undefined ? (res as any).data : res),
      catchError(this.handleError)
    );
  }

  patch<T>(endpoint: string, data?: any): Observable<T> {
    return this.http.patch<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data, {
      headers: this.getHeaders(),
      withCredentials: true
    }).pipe(
      map(res => (res as any).data !== undefined ? (res as any).data : res),
      catchError(this.handleError)
    );
  }

  delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, {
      headers: this.getHeaders(),
      withCredentials: true
    }).pipe(
      map(res => (res as any).data !== undefined ? (res as any).data : res),
      catchError(this.handleError)
    );
  }

  getBlob(endpoint: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}${endpoint}`, {
      headers: this.getHeaders(),
      withCredentials: true,
      responseType: 'blob'
    }).pipe(
      catchError(this.handleError)
    );
  }

  private handleError = (error: any): Observable<never> => {
    let errorMessage = 'Ha ocurrido un error';
    if (error.error?.error) {
      errorMessage = error.error.error;
    } else if (error.message) {
      errorMessage = error.message;
    }
    return throwError(() => new Error(errorMessage));
  };
}

