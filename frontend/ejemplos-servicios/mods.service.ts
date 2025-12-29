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
  config_file_path?: string;
  config_format?: string;
  default_config?: string;
}

export interface ModConfig {
  mod_name: string;
  mod_pool: {
    id: number;
    display_name: string;
    mod_type: string;
  };
  config_file_path: string;
  config_format: string;
  config_content: string;
  file_exists: boolean;
  is_default: boolean;
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
      map(response => response.data || response.message)
    );
  }

  /**
   * Habilitar mod
   */
  enableMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/enable/`, { mod_name: modName }).pipe(
      map(response => response.data || response.message)
    );
  }

  /**
   * Deshabilitar mod
   */
  disableMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/disable/`, { mod_name: modName }).pipe(
      map(response => response.data || response.message)
    );
  }

  /**
   * Eliminar mod
   */
  deleteMod(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/delete/`, { mod_name: modName }).pipe(
      map(response => response.data || response.message)
    );
  }

  /**
   * Obtener configuración de un mod
   */
  getModConfig(serverId: number, modName: string): Observable<ModConfig> {
    return this.api.get<ModConfig>(`/servers/${serverId}/mods/config/?mod_name=${encodeURIComponent(modName)}`).pipe(
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
      map(response => response.data || response.message)
    );
  }

  /**
   * Resetear configuración de un mod
   */
  resetModConfig(serverId: number, modName: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/config/reset/`, { mod_name: modName }).pipe(
      map(response => response.data || response.message)
    );
  }

  /**
   * Listar pool de mods
   */
  getModsPool(serverType?: string, category?: string): Observable<ModPool[]> {
    let endpoint = '/mods/pool/';
    const params: string[] = [];
    
    if (serverType) params.push(`server_type=${serverType}`);
    if (category) params.push(`category=${category}`);
    
    if (params.length > 0) {
      endpoint += '?' + params.join('&');
    }
    
    return this.api.get<ModPool[]>(endpoint, false).pipe(
      map(response => response.data || [])
    );
  }

  /**
   * Obtener categorías del pool
   */
  getModsPoolCategories(): Observable<string[]> {
    return this.api.get<string[]>('/mods/pool/categories/', false).pipe(
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

