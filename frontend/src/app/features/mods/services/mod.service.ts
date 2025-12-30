import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Mod } from '../../../shared/models/mod.model';

export interface ModConfig {
  mod_name: string;
  config_content: string;
  config_file_path: string;
}

export interface UpdateModConfigRequest {
  config_content: string;
}

@Injectable({
  providedIn: 'root'
})
export class ModService {
  constructor(private api: ApiService) {}

  getMods(serverId: number): Observable<Mod[]> {
    return this.api.get<Mod[]>(`/servers/${serverId}/mods/`);
  }

  uploadMod(serverId: number, file: File): Observable<any> {
    const formData = new FormData();
    formData.append('mod_file', file);
    return this.api.post(`/servers/${serverId}/mods/upload/`, formData);
  }

  enableMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/enable/`, { mod_name: modName });
  }

  disableMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/disable/`, { mod_name: modName });
  }

  deleteMod(serverId: number, mod: Mod): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/delete/`, {
      mod_name: mod.name,
      file_path: mod.file_path || mod.path,
      enabled: mod.enabled
    });
  }

  getModConfig(serverId: number, modName: string): Observable<ModConfig> {
    return this.api.get<ModConfig>(`/servers/${serverId}/mods/config/`, { mod_name: modName });
  }

  updateModConfig(serverId: number, modName: string, data: UpdateModConfigRequest): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/config/update/`, {
      mod_name: modName,
      ...data
    });
  }

  resetModConfig(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/config/reset/`, { mod_name: modName });
  }
}

