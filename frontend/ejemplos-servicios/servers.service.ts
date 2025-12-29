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

export interface ServerStatus {
  online: boolean;
  player_count: number;
  max_players: number;
  rcon_connected: boolean;
  docker_running: boolean;
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
  getServerStatus(serverId: number): Observable<ServerStatus> {
    return this.api.get<ServerStatus>(`/servers/${serverId}/status/`).pipe(
      map(response => response.data)
    );
  }

  /**
   * Obtener estadísticas de un servidor
   */
  getServerStats(serverId: number): Observable<any> {
    return this.api.get(`/servers/${serverId}/stats/`).pipe(
      map(response => response.data)
    );
  }

  /**
   * Controlar servidor (start, stop, restart, pause, unpause)
   */
  controlServer(serverId: number, action: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/control/${action}/`).pipe(
      map(response => response.data || response.message)
    );
  }

  /**
   * Obtener información del contenedor Docker
   */
  getContainerInfo(serverId: number): Observable<any> {
    return this.api.get(`/servers/${serverId}/container/`).pipe(
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

