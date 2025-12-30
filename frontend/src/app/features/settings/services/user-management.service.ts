import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { User, UserServerRole } from '../../../shared/models';

export interface CreateDjangoUserRequest {
  username: string;
  email?: string;
  password: string;
  is_staff?: boolean;
  is_active?: boolean;
}

export interface UpdateDjangoUserRequest {
  email?: string;
  is_staff?: boolean;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  new_password: string;
}

export interface AssignRoleRequest {
  user_id: number;
  role: 'admin' | 'moderator' | 'viewer';
}

export interface UpdateRoleRequest {
  role: 'admin' | 'moderator' | 'viewer';
}

export interface ServerRole {
  id: number;
  user: User;
  server: {
    id: number;
    name: string;
  };
  role: 'admin' | 'moderator' | 'viewer';
  created_at: string;
}

export interface UserPermissions {
  user: User;
  servers: Array<{
    server_id: number;
    server_name: string;
    role: 'admin' | 'moderator' | 'viewer';
    permissions: string[];
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class UserManagementService {
  constructor(private api: ApiService) {}

  // Gestión de usuarios Django
  getUsers(): Observable<User[]> {
    return this.api.get<User[]>('/users/');
  }

  getUserDetail(userId: number): Observable<User & { roles: ServerRole[] }> {
    return this.api.get<User & { roles: ServerRole[] }>(`/users/${userId}/`);
  }

  createUser(data: CreateDjangoUserRequest): Observable<User> {
    return this.api.post<User>('/users/create/', data);
  }

  updateUser(userId: number, data: UpdateDjangoUserRequest): Observable<User> {
    return this.api.put<User>(`/users/${userId}/update/`, data);
  }

  deleteUser(userId: number): Observable<any> {
    return this.api.delete(`/users/${userId}/delete/`);
  }

  changePassword(userId: number, data: ChangePasswordRequest): Observable<any> {
    return this.api.post(`/users/${userId}/change-password/`, data);
  }

  getUserRoles(userId: number): Observable<{ user: User; roles: ServerRole[] }> {
    return this.api.get<{ user: User; roles: ServerRole[] }>(`/users/${userId}/roles/`);
  }

  getMyPermissions(): Observable<UserPermissions> {
    return this.api.get<UserPermissions>('/users/me/permissions/');
  }

  // Gestión de roles en servidores
  getServerRoles(serverId: number): Observable<ServerRole[]> {
    return this.api.get<ServerRole[]>(`/servers/${serverId}/roles/`);
  }

  assignRole(serverId: number, data: AssignRoleRequest): Observable<ServerRole> {
    return this.api.post<ServerRole>(`/servers/${serverId}/roles/assign/`, data);
  }

  updateRole(serverId: number, roleId: number, data: UpdateRoleRequest): Observable<ServerRole> {
    return this.api.put<ServerRole>(`/servers/${serverId}/roles/${roleId}/update/`, data);
  }

  removeRole(serverId: number, roleId: number): Observable<any> {
    return this.api.delete(`/servers/${serverId}/roles/${roleId}/remove/`);
  }
}

