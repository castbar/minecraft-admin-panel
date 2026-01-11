import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { LogsService } from '../../services/logs.service';
import { interval, Subscription } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { addIcons } from 'ionicons';
import { pauseOutline, playOutline, refreshOutline, trashOutline, sendOutline } from 'ionicons/icons';

interface ChatMessage {
  timestamp: string;
  player: string;
  message: string;
  raw: string;
}

@Component({
  selector: 'app-chat-viewer',
  standalone: true,
  imports: [CommonModule, IonicModule],
  templateUrl: './chat-viewer.component.html',
  styleUrls: ['./chat-viewer.component.scss']
})
export class ChatViewerComponent implements OnInit, OnDestroy, AfterViewChecked {
  @Input() serverId!: number;
  @Input() autoRefresh: boolean = true;
  @Input() refreshInterval: number = 2000; // 2 segundos
  @Input() maxMessages: number = 100;
  @ViewChild('chatContainer', { static: false }) chatContainer!: ElementRef;

  chatMessages: ChatMessage[] = [];
  isLoading = false;
  private subscription?: Subscription;
  private allLogs: string[] = [];
  private shouldScroll = false;
  private previousMessagesCount = 0;

  constructor(private logsService: LogsService) {
    addIcons({
      pauseOutline,
      playOutline,
      refreshOutline,
      trashOutline,
      sendOutline,
    });
  }

  ngOnInit(): void {
    this.loadChat();
    if (this.autoRefresh) {
      this.startAutoRefresh();
    }
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  loadChat(): void {
    if (!this.serverId) return;
    
    this.isLoading = true;
    this.logsService.getLogs(this.serverId, 200).pipe(
      catchError(() => of({ data: [] }))
    ).subscribe({
      next: (response: any) => {
        this.allLogs = response.data || response || [];
        this.filterChatMessages();
        this.isLoading = false;
        // Scroll al final después de cargar inicialmente
        setTimeout(() => {
          this.shouldScroll = true;
        }, 100);
      },
      error: () => {
        this.isLoading = false;
        this.chatMessages = [];
      }
    });
  }

  filterChatMessages(): void {
    // Patrones mejorados para capturar mensajes de chat
    // Formato real: 03:20:23[Not Secure] <Chrsx3> hola
    // O: [HH:MM:SS] [Server thread/INFO]: <player> mensaje
    const chatPatterns = [
      // Patrón para formato: [HH:MM:SS] [Server thread/INFO]: [Not Secure] <player> mensaje
      /\[(\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\]: \[Not Secure\] <([^>]+)> (.+)/,
      // Patrón para formato: HH:MM:SS[Not Secure] <player> mensaje (sin brackets iniciales)
      /^(\d{2}:\d{2}:\d{2})\[Not Secure\] <([^>]+)> (.+)$/,
      // Patrón estándar: [HH:MM:SS] [Server thread/INFO]: <player> mensaje
      /\[(\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\]: <([^>]+)> (.+)/,
      // Patrón alternativo: [HH:MM:SS] [Server thread/INFO]: [Server] mensaje
      /\[(\d{2}:\d{2}:\d{2})\] \[Server thread\/INFO\]: \[Server\] (.+)/,
      // Patrón con otros threads: [HH:MM:SS] [Thread/INFO]: <player> mensaje
      /\[(\d{2}:\d{2}:\d{2})\] \[[^\]]+\/INFO\]: <([^>]+)> (.+)/,
      // Patrón sin brackets: [HH:MM:SS] [INFO]: <player> mensaje
      /\[(\d{2}:\d{2}:\d{2})\] \[INFO\]: <([^>]+)> (.+)/,
    ];

    const newMessages: ChatMessage[] = [];
    const seenMessages = new Set<string>();

    for (const log of this.allLogs) {
      // Limpiar el log de caracteres extraños y espacios múltiples
      const cleanLog = log.trim();
      
      for (const pattern of chatPatterns) {
        const match = cleanLog.match(pattern);
        if (match) {
          const timestamp = match[1] || '';
          const player = match[2] || 'Server';
          const message = (match[3] || match[2] || '').trim();

          // Evitar duplicados y mensajes vacíos
          if (!message) continue;
          
          const messageKey = `${timestamp}-${player}-${message}`;
          if (!seenMessages.has(messageKey)) {
            seenMessages.add(messageKey);
            newMessages.push({
              timestamp,
              player,
              message,
              raw: cleanLog
            });
          }
          break;
        }
      }
    }

    // Verificar si hay nuevos mensajes para hacer scroll
    const hadNewMessages = newMessages.length > this.chatMessages.length;
    
    // Ordenar por timestamp y tomar los últimos N mensajes
    this.chatMessages = newMessages
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp))
      .slice(-this.maxMessages);
    
    // Activar scroll si hay nuevos mensajes
    if (hadNewMessages && this.chatMessages.length > this.previousMessagesCount) {
      this.shouldScroll = true;
    }
    this.previousMessagesCount = this.chatMessages.length;
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll && this.chatContainer) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  scrollToBottom(): void {
    try {
      if (this.chatContainer && this.chatContainer.nativeElement) {
        const element = this.chatContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    } catch (err) {
      console.error('Error scrolling to bottom:', err);
    }
  }

  startAutoRefresh(): void {
    this.stopAutoRefresh();
    this.subscription = interval(this.refreshInterval).pipe(
      switchMap(() => this.logsService.getLogs(this.serverId, 200).pipe(
        catchError(() => of({ data: [] }))
      ))
    ).subscribe({
      next: (response: any) => {
        const previousMessagesCount = this.chatMessages.length;
        this.allLogs = response.data || response || [];
        
        // Filtrar siempre para detectar nuevos mensajes incluso si el número de logs es el mismo
        // (puede haber nuevos mensajes en las mismas líneas)
        this.filterChatMessages();
        
        // Activar scroll si hay nuevos mensajes
        if (this.chatMessages.length > previousMessagesCount) {
          this.shouldScroll = true;
        }
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

  clearChat(): void {
    this.chatMessages = [];
    this.allLogs = [];
    this.previousMessagesCount = 0;
  }

  trackByMessage(index: number, msg: ChatMessage): string {
    return `${msg.timestamp}-${msg.player}-${msg.message}`;
  }
}

