import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Server, ServerStatus, ServerStats } from '../../../shared/models';

export interface CreateServerRequest {
  name: string;
  host: string;
  port: number;
  rcon_port: number;
  rcon_password: string;
  server_type: 'vanilla' | 'fabric' | 'forge' | 'bukkit' | 'spigot' | 'paper';
  version: string;
  max_players: number;
  difficulty: 'peaceful' | 'easy' | 'normal' | 'hard';
  pvp_enabled: boolean;
  whitelist_enabled: boolean;
}

export interface ServerControlAction {
  action: 'start' | 'stop' | 'restart' | 'pause' | 'unpause';
}

@Injectable({
  providedIn: 'root'
})
export class ServerService {
  constructor(private api: ApiService) {}

  getServers(): Observable<Server[]> {
    return this.api.get<Server[]>('/servers/');
  }

  createServer(data: CreateServerRequest): Observable<{ server_id: number; data: Server }> {
    return this.api.post<{ server_id: number; data: Server }>('/servers/create/', data);
  }

  getServerStatus(serverId: number): Observable<ServerStatus> {
    return this.api.get<ServerStatus>(`/servers/${serverId}/status/`);
  }

  getServerStats(serverId: number): Observable<ServerStats> {
    return this.api.get<ServerStats>(`/servers/${serverId}/stats/`);
  }

  controlServer(serverId: number, action: ServerControlAction['action']): Observable<any> {
    return this.api.post(`/servers/${serverId}/control/${action}/`, {});
  }

  getContainerInfo(serverId: number): Observable<any> {
    return this.api.get(`/servers/${serverId}/container/`);
  }

  getServerSettings(serverId: number): Observable<Server> {
    return this.api.get<Server>(`/servers/${serverId}/settings/`);
  }

  updateServerSettings(serverId: number, data: Partial<Server>): Observable<Server> {
    return this.api.put<Server>(`/servers/${serverId}/settings/update/`, data);
  }

  deleteServer(serverId: number): Observable<any> {
    return this.api.delete(`/servers/${serverId}/delete/`);
  }
}

