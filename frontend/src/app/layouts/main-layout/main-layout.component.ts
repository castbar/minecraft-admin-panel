import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonMenu, 
  IonMenuButton,
  IonMenuToggle, 
  IonButton, 
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonSelect,
  IonSelectOption,
  MenuController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { 
  menuOutline, 
  logOutOutline, 
  serverOutline,
  settingsOutline,
  peopleOutline,
  cubeOutline,
  folderOutline,
  homeOutline,
  chevronBackOutline,
  chevronForwardOutline,
  checkmarkCircleOutline
} from 'ionicons/icons';
import { AuthService } from '../../core/services/auth.service';
import { ServerService } from '../../features/servers/services/server.service';
import { Observable, BehaviorSubject, combineLatest } from 'rxjs';
import { map, tap, catchError } from 'rxjs/operators';
import { Server } from '../../shared/models';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-main-layout',
  templateUrl: './main-layout.component.html',
  styleUrls: ['./main-layout.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonMenu,
    IonMenuButton,
    IonMenuToggle,
    IonButton,
    IonIcon,
    IonItem,
    IonLabel,
    IonList,
    IonSelect,
    IonSelectOption
  ]
})
export class MainLayoutComponent implements OnInit {
  sidebarCollapsed$ = new BehaviorSubject<boolean>(false);
  
  currentUser$ = this.authService.authState.pipe(
    map(state => state.user)
  );
  
  currentServerId$ = this.authService.authState.pipe(
    map(state => state.currentServerId)
  );

  servers$: Observable<Server[]> = this.serverService.getServers().pipe(
    tap(servers => {
      // Si hay servidores y no hay uno seleccionado, seleccionar el primero
      if (servers.length > 0 && !this.authService.currentServerId) {
        this.authService.setCurrentServerId(servers[0].id);
      }
    }),
    catchError(error => {
      this.toast.error('Error al cargar servidores');
      return [];
    })
  );

  currentServer$: Observable<Server | null> = combineLatest([
    this.servers$,
    this.currentServerId$
  ]).pipe(
    map(([servers, serverId]) => {
      if (!serverId || servers.length === 0) return null;
      return servers.find(s => s.id === serverId) || null;
    })
  );

  constructor(
    private authService: AuthService,
    private serverService: ServerService,
    private menuController: MenuController,
    private toast: ToastService
  ) {
    addIcons({
      menuOutline,
      logOutOutline,
      serverOutline,
      settingsOutline,
      peopleOutline,
      cubeOutline,
      folderOutline,
      homeOutline,
      chevronBackOutline,
      chevronForwardOutline,
      checkmarkCircleOutline
    });
  }

  ngOnInit(): void {
    // Cargar servidores automáticamente
  }

  async logout(): Promise<void> {
    await this.authService.logout();
  }

  onServerChange(event: any): void {
    const serverId = event.detail.value;
    this.authService.setCurrentServerId(serverId);
  }

  toggleSidebar(): void {
    const current = this.sidebarCollapsed$.value;
    this.sidebarCollapsed$.next(!current);
  }

  get sidebarCollapsed(): boolean {
    return this.sidebarCollapsed$.value;
  }
}

