export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  data?: {
    user: {
      id: number;
      username: string;
      email?: string;
      is_staff: boolean;
    };
  };
  user?: {
    id: number;
    username: string;
    email?: string;
    is_staff: boolean;
  };
  error?: string;
}

import { User } from './user.model';

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  currentServerId: number | null;
}

