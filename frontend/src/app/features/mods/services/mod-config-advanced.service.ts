import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface ServerModConfig {
  id: number;
  server_id: number;
  mod_name: string;
  config_file_path: string;
  config_content: string;
  template_id?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateServerModConfigRequest {
  mod_name: string;
  config_file_path: string;
  config_content: string;
  template_id?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ModConfigAdvancedService {
  constructor(private api: ApiService) {}

  getServerConfigs(serverId: number): Observable<ServerModConfig[]> {
    return this.api.get<ServerModConfig[]>(`/servers/${serverId}/mods/configs/`);
  }

  createServerConfig(serverId: number, data: CreateServerModConfigRequest): Observable<ServerModConfig> {
    return this.api.post<ServerModConfig>(`/servers/${serverId}/mods/configs/create/`, data);
  }

  getServerConfig(serverId: number, configId: number): Observable<ServerModConfig> {
    return this.api.get<ServerModConfig>(`/servers/${serverId}/mods/configs/${configId}/`);
  }

  applyConfig(serverId: number, configId: number): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/configs/${configId}/apply/`, {});
  }

  applyAllConfigs(serverId: number): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/configs/apply-all/`, {});
  }

  updateServerConfig(serverId: number, configId: number, data: Partial<CreateServerModConfigRequest>): Observable<ServerModConfig> {
    return this.api.put<ServerModConfig>(`/servers/${serverId}/mods/configs/${configId}/update/`, data);
  }

  deleteServerConfig(serverId: number, configId: number): Observable<any> {
    return this.api.delete(`/servers/${serverId}/mods/configs/${configId}/delete/`);
  }
}

