import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../../shared/models';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    });
  }

  get<T>(endpoint: string, params?: any): Observable<T> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] !== null && params[key] !== undefined) {
          httpParams = httpParams.set(key, params[key].toString());
        }
      });
    }
    return this.http
      .get<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, {
        headers: this.getHeaders(),
        params: httpParams,
        withCredentials: true,
      })
      .pipe(
        map((res) => {
          const extracted =
            (res as any).data !== undefined ? (res as any).data : res;
          return extracted;
        }),
        catchError(this.handleError)
      );
  }

  post<T>(endpoint: string, data?: any): Observable<T> {
    let headers = this.getHeaders();

    if (data instanceof FormData) {
      headers = headers.delete('Content-Type');
    }

    const url = `${this.baseUrl}${endpoint}`;
    console.log('ApiService.post - URL:', url);
    console.log('ApiService.post - Data:', data);
    console.log('ApiService.post - Headers:', headers);

    return this.http
      .post<ApiResponse<T>>(url, data, {
        headers,
        withCredentials: true,
      })
      .pipe(
        map((res) => {
          console.log('ApiService.post - Respuesta recibida:', res);
          // Para endpoints de settings/update, devolver la respuesta completa
          // porque incluye requires_restart y applied_via_rcon
          if (endpoint.includes('/settings/update/')) {
            console.log('ApiService.post - Devolviendo respuesta completa para settings/update');
            return res as any;
          }
          // Para otros endpoints, devolver solo data si existe
          const mapped =
            (res as any).data !== undefined ? (res as any).data : res;
          console.log('ApiService.post - Datos mapeados:', mapped);
          return mapped;
        }),
        catchError((error) => {
          console.error('ApiService.post - Error capturado:', error);
          return this.handleError(error);
        })
      );
  }

  put<T>(endpoint: string, data?: any): Observable<T> {
    return this.http
      .put<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data, {
        headers: this.getHeaders(),
        withCredentials: true,
      })
      .pipe(
        map((res) =>
          (res as any).data !== undefined ? (res as any).data : res
        ),
        catchError(this.handleError)
      );
  }

  patch<T>(endpoint: string, data?: any): Observable<T> {
    return this.http
      .patch<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data, {
        headers: this.getHeaders(),
        withCredentials: true,
      })
      .pipe(
        map((res) =>
          (res as any).data !== undefined ? (res as any).data : res
        ),
        catchError(this.handleError)
      );
  }

  delete<T>(endpoint: string): Observable<T> {
    return this.http
      .delete<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, {
        headers: this.getHeaders(),
        withCredentials: true,
      })
      .pipe(
        map((res) =>
          (res as any).data !== undefined ? (res as any).data : res
        ),
        catchError(this.handleError)
      );
  }

  getBlob(endpoint: string): Observable<Blob> {
    return this.http
      .get(`${this.baseUrl}${endpoint}`, {
        headers: this.getHeaders(),
        withCredentials: true,
        responseType: 'blob',
      })
      .pipe(catchError(this.handleError));
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
