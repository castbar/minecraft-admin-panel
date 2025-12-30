import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface ModPool {
  id: number;
  name: string;
  display_name?: string;
  description?: string;
  category: string;
  author?: string;
  version?: string;
  download_url?: string;
  compatible_servers: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateModPoolRequest {
  name: string;
  description?: string;
  category: string;
  author?: string;
  version?: string;
  download_url?: string;
  compatible_servers: string[];
}

@Injectable({
  providedIn: 'root'
})
export class ModPoolService {
  constructor(private api: ApiService) {}

  getModsPool(params?: { server_type?: string; category?: string; search?: string }): Observable<ModPool[]> {
    return this.api.get<ModPool[]>('/mods/pool/', params);
  }

  getCategories(): Observable<string[]> {
    return this.api.get<string[]>('/mods/pool/categories/');
  }

  getModDetail(modId: number): Observable<ModPool> {
    return this.api.get<ModPool>(`/mods/pool/${modId}/`);
  }

  createMod(data: CreateModPoolRequest): Observable<ModPool> {
    return this.api.post<ModPool>('/mods/pool/create/', data);
  }

  installMod(serverId: number, modPoolId: number): Observable<any> {
    return this.api.post(`/servers/${serverId}/mods/pool/install/`, { mod_pool_id: modPoolId });
  }
}

