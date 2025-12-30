import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({
  providedIn: 'root'
})
export class LogsService {
  constructor(private api: ApiService) {}

  getLogs(serverId: number, lines?: number): Observable<string[]> {
    const params = lines ? { lines } : {};
    return this.api.get<string[]>(`/servers/${serverId}/logs/`, params);
  }
}

