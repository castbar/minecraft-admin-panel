import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface WhitelistPlayer {
  username: string;
  uuid?: string;
}

export interface AddWhitelistRequest {
  username: string;
}

export interface RemoveWhitelistRequest {
  username: string;
}

@Injectable({
  providedIn: 'root'
})
export class WhitelistService {
  constructor(private api: ApiService) {}

  getWhitelist(serverId: number): Observable<WhitelistPlayer[]> {
    return this.api.get<WhitelistPlayer[]>(`/servers/${serverId}/whitelist/`);
  }

  addToWhitelist(serverId: number, username: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/whitelist/add/`, { username });
  }

  removeFromWhitelist(serverId: number, username: string): Observable<any> {
    return this.api.post(`/servers/${serverId}/whitelist/remove/`, { username });
  }
}

