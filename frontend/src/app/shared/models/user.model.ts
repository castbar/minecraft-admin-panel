export interface User {
  id: number;
  username: string;
  email?: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
}

export interface MinecraftUser {
  id: number;
  server_id: number;
  username: string;
  email?: string;
  is_active: boolean;
  is_operator: boolean;
  created_at: string;
  updated_at: string;
}

import { Server } from './server.model';

export interface UserServerRole {
  id: number;
  user_id: number;
  server_id: number;
  role: 'admin' | 'moderator' | 'viewer';
  server?: Server;
}

