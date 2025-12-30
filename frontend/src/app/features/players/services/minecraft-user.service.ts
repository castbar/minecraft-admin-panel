import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { MinecraftUser } from '../../../shared/models';

export interface CreateMinecraftUserRequest {
  username: string;
  email: string;
  password?: string;
  is_operator?: boolean;
}

export interface UpdateMinecraftUserRequest {
  username?: string;
  email?: string;
  is_operator?: boolean;
  is_active?: boolean;
}

export interface SetPasswordRequest {
  token: string;
  password: string;
}

@Injectable({
  providedIn: 'root'
})
export class MinecraftUserService {
  constructor(private api: ApiService) {}

  getUsers(serverId: number): Observable<MinecraftUser[]> {
    return this.api.get<MinecraftUser[]>(`/servers/${serverId}/users/`);
  }

  createUser(serverId: number, data: CreateMinecraftUserRequest): Observable<MinecraftUser> {
    return this.api.post<MinecraftUser>(`/servers/${serverId}/users/create/`, data);
  }

  setPassword(serverId: number, data: SetPasswordRequest): Observable<any> {
    return this.api.post(`/servers/${serverId}/users/set-password/`, data);
  }

  updateUser(serverId: number, userId: number, data: UpdateMinecraftUserRequest): Observable<MinecraftUser> {
    return this.api.put<MinecraftUser>(`/servers/${serverId}/users/${userId}/update/`, data);
  }

  deleteUser(serverId: number, userId: number): Observable<any> {
    return this.api.delete(`/servers/${serverId}/users/${userId}/delete/`);
  }
}

