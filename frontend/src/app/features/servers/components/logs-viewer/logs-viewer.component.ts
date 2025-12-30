import { Component, Input, OnInit, OnDestroy } from '@angular/core';
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
export class LogsViewerComponent implements OnInit, OnDestroy {
  @Input() serverId!: number;
  @Input() autoRefresh: boolean = true;
  @Input() refreshInterval: number = 2000; // 2 segundos
  @Input() maxLines: number = 100;

  logs: string[] = [];
  isLoading = false;
  private subscription?: Subscription;

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
        this.toast.error('Error al cargar logs');
        return of([]);
      })
    ).subscribe({
      next: (response: any) => {
        this.logs = response.data || response || [];
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  startAutoRefresh(): void {
    this.stopAutoRefresh();
    this.subscription = interval(this.refreshInterval).pipe(
      switchMap(() => this.logsService.getLogs(this.serverId, this.maxLines).pipe(
        catchError(() => of([]))
      ))
    ).subscribe({
      next: (response: any) => {
        this.logs = response.data || response || [];
      }
    });
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

