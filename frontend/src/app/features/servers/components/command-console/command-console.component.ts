import { Component, Input, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { CommandService } from '../../services/command.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ToastService } from '../../../../core/services/toast.service';
import { FormsModule } from '@angular/forms';

interface CommandHistory {
  command: string;
  output: string;
  timestamp: Date;
  success: boolean;
}

@Component({
  selector: 'app-command-console',
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule],
  templateUrl: './command-console.component.html',
  styleUrls: ['./command-console.component.scss'],
})
export class CommandConsoleComponent implements OnInit {
  @Input() serverId!: number;
  @ViewChild('commandInput', { static: false })
  commandInput?: ElementRef<HTMLIonInputElement>;
  @ViewChild('outputContainer', { static: false })
  outputContainer?: ElementRef<HTMLDivElement>;

  command: string = '';
  history: CommandHistory[] = [];
  isExecuting = false;
  maxHistory = 100;

  constructor(
    private commandService: CommandService,
    private authService: AuthService,
    private toast: ToastService
  ) {}

  ngOnInit(): void {
    // Cargar historial desde localStorage si existe
    const saved = localStorage.getItem(`command_history_${this.serverId}`);
    if (saved) {
      try {
        this.history = JSON.parse(saved).map((h: any) => ({
          ...h,
          timestamp: new Date(h.timestamp),
        }));
      } catch (e) {
        // Ignorar errores de parseo
      }
    }
  }

  executeCommand(): void {
    if (!this.command.trim() || !this.serverId || this.isExecuting) return;

    const commandText = this.command.trim();
    this.isExecuting = true;

    this.commandService.executeCommand(this.serverId, commandText).subscribe({
      next: (response: any) => {
        const result: CommandHistory = {
          command: commandText,
          output:
            response.data?.output ||
            response.output ||
            'Comando ejecutado correctamente',
          timestamp: new Date(),
          success: response.success !== false,
        };

        this.history.push(result);
        if (this.history.length > this.maxHistory) {
          this.history.shift();
        }

        this.saveHistory();
        this.command = '';
        this.isExecuting = false;
        this.scrollToBottom();

        if (!result.success) {
          this.toast.error(result.output);
        } else {
          this.toast.success('Comando ejecutado');
        }
      },
      error: (error) => {
        const result: CommandHistory = {
          command: commandText,
          output: error.message || 'Error al ejecutar comando',
          timestamp: new Date(),
          success: false,
        };

        this.history.push(result);
        if (this.history.length > this.maxHistory) {
          this.history.shift();
        }

        this.saveHistory();
        this.command = '';
        this.isExecuting = false;
        this.scrollToBottom();
        this.toast.error('Error al ejecutar comando');
      },
    });
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.executeCommand();
    }
  }

  clearHistory(): void {
    this.history = [];
    this.saveHistory();
    this.toast.success('Historial limpiado');
  }

  private saveHistory(): void {
    localStorage.setItem(
      `command_history_${this.serverId}`,
      JSON.stringify(this.history)
    );
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.outputContainer) {
        const element = this.outputContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 100);
  }

  formatTimestamp(date: Date): string {
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }
}
