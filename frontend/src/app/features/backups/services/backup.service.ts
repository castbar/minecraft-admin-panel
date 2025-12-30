import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface Backup {
  id: number;
  server_id: number;
  filename: string;
  file_path: string;
  size: number;
  created_at: string;
  created_by?: number;
}

export interface BackupSchedule {
  id: number;
  server_id: number;
  schedule_type: 'daily' | 'weekly' | 'monthly';
  schedule_time: string;
  keep_count: number;
  enabled: boolean;
  last_run?: string;
  next_run?: string;
}

export interface CreateBackupRequest {
  description?: string;
}

export interface RestoreBackupRequest {
  backup_id: number;
}

@Injectable({
  providedIn: 'root'
})
export class BackupService {
  constructor(private api: ApiService) {}

  getBackups(serverId: number): Observable<Backup[]> {
    return this.api.get<Backup[]>(`/servers/${serverId}/backups/`);
  }

  createBackup(serverId: number, data?: CreateBackupRequest): Observable<Backup> {
    return this.api.post<Backup>(`/servers/${serverId}/backups/create/`, data || {});
  }

  restoreBackup(serverId: number, backupId: number): Observable<any> {
    return this.api.post(`/servers/${serverId}/backups/${backupId}/restore/`, {});
  }

  downloadBackup(serverId: number, backupId: number): Observable<Blob> {
    return this.api.getBlob(`/servers/${serverId}/backups/${backupId}/download/`);
  }

  deleteBackup(serverId: number, backupId: number): Observable<any> {
    return this.api.delete(`/servers/${serverId}/backups/${backupId}/delete/`);
  }

  getBackupSchedules(serverId: number): Observable<BackupSchedule[]> {
    return this.api.get<BackupSchedule[]>(`/servers/${serverId}/backup-schedules/`);
  }

  createBackupSchedule(serverId: number, data: Partial<BackupSchedule>): Observable<BackupSchedule> {
    return this.api.post<BackupSchedule>(`/servers/${serverId}/backup-schedules/create/`, data);
  }

  updateBackupSchedule(serverId: number, scheduleId: number, data: Partial<BackupSchedule>): Observable<BackupSchedule> {
    return this.api.put<BackupSchedule>(`/servers/${serverId}/backup-schedules/${scheduleId}/update/`, data);
  }

  deleteBackupSchedule(serverId: number, scheduleId: number): Observable<any> {
    return this.api.delete(`/servers/${serverId}/backup-schedules/${scheduleId}/delete/`);
  }
}

