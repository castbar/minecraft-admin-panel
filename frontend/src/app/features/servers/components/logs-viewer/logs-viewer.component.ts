import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { LogsService } from '../../services/logs.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ToastService } from '../../../../core/services/toast.service';
import { interval, Subscription } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';

@Component({
  selector: 'app-logs-viewer',
  standalone: true,
  imports: [CommonModule, IonicModule],
  templateUrl: './logs-viewer.component.html',
  styleUrls: ['./logs-viewer.component.scss']
})
export class LogsViewerComponent implements OnInit, OnDestroy, AfterViewChecked {
  @Input() serverId!: number;
  @Input() autoRefresh: boolean = true;
  @Input() refreshInterval: number = 2000; // 2 segundos
  @Input() maxLines: number = 100;
  @ViewChild('logsContainer', { static: false }) logsContainer?: ElementRef<HTMLDivElement>;

  logs: string[] = [];
  filteredLogs: string[] = []; // Logs sin mensajes de chat
  isLoading = false;
  private subscription?: Subscription;
  private shouldScrollToBottom = false;
  private previousLogsLength = 0;

  constructor(
    private logsService: LogsService,
    private authService: AuthService,
    private toast: ToastService
  ) {}

  ngOnInit(): void {
    this.loadLogs();
    if (this.autoRefresh) {
      this.startAutoRefresh();
    }
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  loadLogs(): void {
    if (!this.serverId) return;
    
    this.isLoading = true;
    this.logsService.getLogs(this.serverId, this.maxLines).pipe(
      catchError(error => {
        // No mostrar error si el servidor está apagado (404 o error de conexión)
        // Solo mostrar error si es un error real del servidor
        if (error.status !== 404 && error.status !== 0) {
          this.toast.error('Error al cargar logs');
        }
        return of({ data: [] });
      })
    ).subscribe({
      next: (response: any) => {
        const newLogs = response.data || response || [];
        const hadNewLogs = newLogs.length > this.logs.length;
        this.logs = newLogs;
        this.filterNonChatLogs();
        this.isLoading = false;
        if (hadNewLogs) {
          setTimeout(() => this.scrollToBottom(), 100);
        }
      },
      error: () => {
        this.isLoading = false;
        // No mostrar error, simplemente dejar logs vacíos
        this.logs = [];
      }
    });
  }

  startAutoRefresh(): void {
    this.stopAutoRefresh();
    this.subscription = interval(this.refreshInterval).pipe(
      switchMap(() => this.logsService.getLogs(this.serverId, this.maxLines).pipe(
        catchError(() => of({ data: [] })) // Devolver objeto con data vacía en lugar de array
      ))
    ).subscribe({
      next: (response: any) => {
        const newLogs = response.data || response || [];
        const hadNewLogs = newLogs.length > this.logs.length;
        this.logs = newLogs;
        this.filterNonChatLogs();
        if (hadNewLogs && this.autoRefresh) {
          setTimeout(() => this.scrollToBottom(), 100);
        }
      }
    });
  }

  filterNonChatLogs(): void {
    // Patrones que identifican mensajes de chat (excluir estos de los logs)
    const chatPatterns = [
      /\[Server thread\/INFO\]: <[^>]+>/,
      /\[Server thread\/INFO\]: \[Server\]/,
      /\[[^\]]+\/INFO\]: <[^>]+>/,
      /\[INFO\]: <[^>]+>/,
    ];

    const oldLength = this.filteredLogs.length;
    this.filteredLogs = this.logs.filter(log => {
      // Excluir líneas que coincidan con patrones de chat
      return !chatPatterns.some(pattern => pattern.test(log));
    });
    
    // Si hay nuevos logs, activar scroll automático
    if (this.filteredLogs.length > oldLength) {
      this.shouldScrollToBottom = true;
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom && this.logsContainer) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  scrollToBottom(): void {
    if (this.logsContainer) {
      const element = this.logsContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  stopAutoRefresh(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
      this.subscription = undefined;
    }
  }

  toggleAutoRefresh(): void {
    this.autoRefresh = !this.autoRefresh;
    if (this.autoRefresh) {
      this.startAutoRefresh();
    } else {
      this.stopAutoRefresh();
    }
  }

  clearLogs(): void {
    this.logs = [];
  }
}

