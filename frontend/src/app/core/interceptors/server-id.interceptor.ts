import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const serverIdInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const serverId = authService.currentServerId;

  // Rutas que NO requieren X-Server-ID (listados generales)
  const noServerIdRoutes = [
    '/servers/',           // Lista de servidores
    '/auth/',              // Autenticación
    '/users/',             // Lista de usuarios Django
    '/minecraft/versions/', // Versiones de Minecraft
    '/mods/pool/',         // Pool de mods
    '/mods/templates/',    // Plantillas de mods
  ];

  // Verificar si la ruta NO requiere X-Server-ID
  const isNoServerIdRoute = noServerIdRoutes.some(route => req.url.startsWith(route));

  // Solo agregar header si hay un serverId, no es una ruta estática, y no es una ruta que no requiere serverId
  if (serverId && !req.url.startsWith('http') && !req.url.startsWith('/assets') && !isNoServerIdRoute) {
    const clonedReq = req.clone({
      setHeaders: {
        'X-Server-ID': serverId.toString()
      }
    });
    return next(clonedReq);
  }

  return next(req);
};

