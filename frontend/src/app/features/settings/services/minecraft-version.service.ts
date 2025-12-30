import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface MinecraftVersion {
  id: number;
  version: string;
  version_type: 'release' | 'snapshot' | 'beta' | 'alpha';
  download_url?: string;
  release_date?: string;
  is_latest: boolean;
  created_at: string;
}

export interface CreateVersionRequest {
  version: string;
  version_type: 'release' | 'snapshot' | 'beta' | 'alpha';
  download_url?: string;
  release_date?: string;
}

@Injectable({
  providedIn: 'root'
})
export class MinecraftVersionService {
  constructor(private api: ApiService) {}

  getVersions(): Observable<MinecraftVersion[]> {
    return this.api.get<MinecraftVersion[]>('/minecraft/versions/');
  }

  getLatestVersion(): Observable<MinecraftVersion> {
    return this.api.get<MinecraftVersion>('/minecraft/versions/latest/');
  }

  createVersion(data: CreateVersionRequest): Observable<MinecraftVersion> {
    return this.api.post<MinecraftVersion>('/minecraft/versions/create/', data);
  }
}

