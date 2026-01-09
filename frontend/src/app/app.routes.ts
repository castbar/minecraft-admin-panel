import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { guestGuard } from './core/guards/guest.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadComponent: () => import('./layouts/auth-layout/auth-layout.component').then(m => m.AuthLayoutComponent),
    canActivate: [guestGuard],
    children: [
      {
        path: 'login',
        loadComponent: () => import('./features/auth/login/login.page').then(m => m.LoginPage),
      },
      {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full',
      },
    ],
  },
  {
    path: '',
    loadComponent: () => import('./layouts/main-layout/main-layout.component').then(m => m.MainLayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./features/servers/dashboard/dashboard.page').then(m => m.DashboardPage),
      },
      {
        path: 'servers',
        loadComponent: () => import('./features/servers/server-list/server-list.page').then(m => m.ServerListPage),
      },
      {
        path: 'servers/:id/detail',
        loadComponent: () => import('./features/servers/server-detail/server-detail.page').then(m => m.ServerDetailPage),
      },
      {
        path: 'servers/create',
        loadComponent: () => import('./features/servers/server-create/server-create.page').then(m => m.ServerCreatePage),
      },
      {
        path: 'players',
        loadComponent: () => import('./features/players/player-list/player-list.page').then(m => m.PlayerListPage),
      },
      {
        path: 'mods',
        loadComponent: () => import('./features/mods/mod-list/mod-list.page').then(m => m.ModListPage),
      },
      {
        path: 'backups',
        loadComponent: () => import('./features/backups/backup-list/backup-list.page').then(m => m.BackupListPage),
      },
      {
        path: 'whitelist',
        loadComponent: () => import('./features/servers/whitelist/whitelist.page').then(m => m.WhitelistPage),
      },
      {
        path: 'settings',
        loadComponent: () => import('./features/settings/settings/settings.page').then(m => m.SettingsPage),
      },
      {
        path: 'users',
        loadComponent: () => import('./features/settings/user-management/user-management.page').then(m => m.UserManagementPage),
      },
      {
        path: 'roles',
        loadComponent: () => import('./features/settings/role-management/role-management.page').then(m => m.RoleManagementPage),
      },
      {
        path: 'mods/templates',
        loadComponent: () => import('./features/mods/mod-templates/mod-templates.page').then(m => m.ModTemplatesPage),
      },
      {
        path: 'mods/configs',
        loadComponent: () => import('./features/mods/mod-configs-advanced/mod-configs-advanced.page').then(m => m.ModConfigsAdvancedPage),
      },
      {
        path: 'backups/schedules',
        loadComponent: () => import('./features/backups/backup-schedules/backup-schedules.page').then(m => m.BackupSchedulesPage),
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
