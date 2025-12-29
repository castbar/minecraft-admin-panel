# Servicios para Frontend Ionic

Estos son los servicios TypeScript listos para usar en tu proyecto Ionic.

## Instalación

1. Copia estos archivos a `src/app/services/` en tu proyecto Ionic
2. Instala las dependencias necesarias:

```bash
npm install @ionic/storage-angular
```

## Archivos

- `api.service.ts` - Servicio base para todas las peticiones HTTP
- `auth.service.ts` - Servicio de autenticación
- `servers.service.ts` - Servicio para gestión de servidores
- `mods.service.ts` - Servicio para gestión de mods
- `auth.guard.ts` - Guard para proteger rutas

## Configuración en app.module.ts

```typescript
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { IonicModule, IonicRouteStrategy } from '@ionic/angular';
import { IonicStorageModule } from '@ionic/storage-angular';
import { RouteReuseStrategy } from '@angular/router';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';

// Servicios
import { ApiService } from './services/api.service';
import { AuthService } from './services/auth.service';
import { ServersService } from './services/servers.service';
import { ModsService } from './services/mods.service';
import { AuthGuard } from './guards/auth.guard';

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    IonicModule.forRoot(),
    AppRoutingModule,
    HttpClientModule,
    IonicStorageModule.forRoot()
  ],
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    ApiService,
    AuthService,
    ServersService,
    ModsService,
    AuthGuard
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
```

## Uso Básico

### En un componente:

```typescript
import { Component, OnInit } from '@angular/core';
import { ServersService } from '../services/servers.service';
import { ModsService } from '../services/mods.service';

@Component({
  selector: 'app-mods',
  templateUrl: './mods.page.html',
})
export class ModsPage implements OnInit {
  servers: any[] = [];
  mods: any[] = [];
  serverId: number | null = null;

  constructor(
    private serversService: ServersService,
    private modsService: ModsService
  ) {}

  async ngOnInit() {
    // Cargar servidores
    this.servers = await firstValueFrom(this.serversService.getServers());
    
    // Establecer servidor activo
    if (this.servers.length > 0) {
      this.serverId = this.servers[0].id;
      this.serversService.setActiveServer(this.serverId);
      
      // Cargar mods
      this.mods = await firstValueFrom(this.modsService.getMods(this.serverId));
    }
  }
}
```

## Características

- ✅ Manejo automático de header `X-Server-ID`
- ✅ Autenticación con sesiones Django (cookies)
- ✅ Manejo de errores centralizado
- ✅ Storage para persistir `current_server_id`
- ✅ Soporte para FormData (uploads)
- ✅ TypeScript con tipos definidos

## Notas

- Todas las peticiones incluyen `withCredentials: true` para cookies
- El `X-Server-ID` se agrega automáticamente cuando hay un servidor activo
- Los servicios usan `firstValueFrom` de RxJS para convertir Observables a Promises

