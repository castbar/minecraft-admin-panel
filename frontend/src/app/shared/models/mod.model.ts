export interface Mod {
  id?: number;
  name: string;
  file_path: string;
  enabled: boolean;
  has_config?: boolean;
  config_file_path?: string;
}

export interface ModPool {
  id: number;
  name: string;
  description?: string;
  category: string;
  author?: string;
  version?: string;
  download_url?: string;
  compatible_servers: string[];
  created_at: string;
  updated_at: string;
}

export interface ModConfig {
  mod_name: string;
  config_content: string;
  config_file_path: string;
}

