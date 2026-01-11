export interface AdditionalPort {
  port: number;
  protocol: 'tcp' | 'udp';
  host_port: number;
}

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
  server_port?: number;
  rcon_port?: number;
  rcon_password?: string;
  server_type?: 'vanilla' | 'fabric' | 'forge' | 'bukkit' | 'spigot' | 'paper';
  version?: string;
  max_players?: number;
  motd?: string;
  difficulty?: 'peaceful' | 'easy' | 'normal' | 'hard';
  pvp?: boolean;
  pvp_enabled?: boolean; // Compatibilidad
  whitelist_enabled?: boolean; // Compatibilidad
  enable_whitelist?: boolean;
  view_distance?: number;
  spawn_protection?: number;
  max_world_size?: number;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  auth_mode?: 'whitelist' | 'database' | 'both' | 'public';
  online_mode?: boolean;
  minecraft_version?: string;
  // Propiedades de Docker
  container_name?: string;
  memory_limit_mb?: number;
  java_heap_max_mb?: number;
  java_heap_min_mb?: number;
  additional_ports?: AdditionalPort[];
  // Propiedades adicionales de server.properties
  simulation_distance?: number;
  gamemode?: 'survival' | 'creative' | 'adventure' | 'spectator';
  hardcore?: boolean;
  spawn_monsters?: boolean;
  spawn_animals?: boolean;
  spawn_npcs?: boolean;
  allow_flight?: boolean;
  enable_command_block?: boolean;
  op_permission_level?: number;
  function_permission_level?: number;
  max_tick_time?: number;
  network_compression_threshold?: number;
  enforce_whitelist?: boolean;
  enforce_secure_profile?: boolean;
  log_ips?: boolean;
  player_idle_timeout?: number;
  rate_limit?: number;
  resource_pack?: string;
  resource_pack_prompt?: string;
  force_gamemode?: boolean;
  generate_structures?: boolean;
  allow_nether?: boolean;
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
  tps?: number; // Ticks per second
  mspt?: number; // Milliseconds per tick
  network_io?: {
    rx_bytes: number;
    tx_bytes: number;
  };
}

