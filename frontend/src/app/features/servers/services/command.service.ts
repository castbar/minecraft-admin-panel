import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';

export interface ExecuteCommandRequest {
  command: string;
}

export interface CommandResponse {
  success: boolean;
  output?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class CommandService {
  constructor(private api: ApiService) {}

  executeCommand(serverId: number, command: string): Observable<CommandResponse> {
    return this.api.post<CommandResponse>('/command/', { command }).pipe(
      map((response: any) => {
        // El backend ahora devuelve { success: true, data: { output: ..., command: ... } }
        if (response.data && response.data.output !== undefined) {
          return {
            success: response.success,
            output: response.data.output,
            error: response.error
          };
        }
        // Compatibilidad con formato anterior
        return {
          success: response.success,
          output: response.response || response.output,
          error: response.error
        };
      })
    );
  }
}

