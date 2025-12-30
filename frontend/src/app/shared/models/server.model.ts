export interface Server {
  id: number;
  name: string;
  host: string;
  role?: string;
  is_hidden?: boolean;
  last_accessed?: string;
  is_favorite?: boolean;
  // Campos opcionales (pueden venir de otros endpoints)
  port?: number;
  rcon_port?: number;
  rcon_password?: string;
  server_type?: 'vanilla' | 'fabric' | 'forge' | 'bukkit' | 'spigot' | 'paper';
  version?: string;
  max_players?: number;
  difficulty?: 'peaceful' | 'easy' | 'normal' | 'hard';
  pvp_enabled?: boolean;
  whitelist_enabled?: boolean;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ServerStatus {
  server_id: number;
  is_running: boolean;
  is_rcon_connected: boolean;
  players_online: number;
  max_players: number;
  uptime?: number;
  memory_usage?: number;
  cpu_usage?: number;
}

export interface ServerStats {
  server_id?: number;
  container_id?: string;
  container_status?: string;
  memory_usage?: number;
  memory_max?: number;
  memory_usage_mb?: number;
  memory_max_mb?: number;
  memory_percent?: number;
  cpu_usage?: number;
  network_io?: {
    rx_bytes: number;
    tx_bytes: number;
  };
}

