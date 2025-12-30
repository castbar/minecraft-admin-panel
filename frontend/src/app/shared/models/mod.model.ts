export interface Mod {
  id?: number;
  name: string;
  file_path?: string;
  enabled: boolean;
  has_config?: boolean;
  config_file_path?: string;
  size?: number;
  size_mb?: number;
  path?: string;
  pool_info?: {
    id: number;
    display_name: string;
    mod_type: string;
    category: string;
    has_config: boolean;
    config_file_path?: string;
    config_format?: string;
  };
}

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

export interface ModConfig {
  mod_name: string;
  config_content: string;
  config_file_path: string;
}

