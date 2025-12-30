export interface Backup {
  id: number;
  server_id: number;
  filename: string;
  file_path: string;
  size: number;
  created_at: string;
  created_by?: number;
  name?: string;
  status?: 'completed' | 'failed' | 'pending' | 'running';
  file_size_mb?: number;
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

