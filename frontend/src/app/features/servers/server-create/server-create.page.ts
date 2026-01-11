import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import {
  IonContent,
  IonHeader,
  IonTitle,
  IonToolbar,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonItem,
  IonLabel,
  IonInput,
  IonSelect,
  IonSelectOption,
  IonToggle,
  IonButton,
  IonList,
  IonIcon,
  IonNote,
  IonSpinner,
  AlertController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { helpCircleOutline, addCircleOutline, trashOutline } from 'ionicons/icons';
import { LoadingController } from '@ionic/angular';
import { ServerService } from '../services/server.service';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { CreateServerRequest } from '../services/server.service';

@Component({
  selector: 'app-server-create',
  templateUrl: './server-create.page.html',
  styleUrls: ['./server-create.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonContent,
    IonHeader,
    IonTitle,
    IonToolbar,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonItem,
    IonLabel,
    IonInput,
    IonSelect,
    IonSelectOption,
    IonToggle,
    IonButton,
    IonList,
    IonIcon,
    IonNote,
    IonSpinner
  ]
})
export class ServerCreatePage {
  serverData: CreateServerRequest & {
    memory_limit_mb?: number;
    java_heap_max_mb?: number;
  } = {
    name: '',
    host: '',
    port: 0, // 0 o null = auto-asignar puerto
    rcon_port: 0, // 0 o null = auto-asignar puerto
    rcon_password: '',
    server_type: 'vanilla',
    version: 'latest',
    max_players: 20,
    difficulty: 'normal',
    pvp_enabled: false,
    whitelist_enabled: true,
    additional_ports: []
  };
  
  autoAssignPorts = true; // Por defecto auto-asignar puertos

  additionalPorts: Array<{ port: number; protocol: 'tcp' | 'udp'; host_port: number }> = [];

  recommendedMemory: { memory_limit_mb: number; java_heap_max_mb: number; java_heap_min_mb: number } | null = null;
  maxPlayersRecommended: number = 0;
  isCreating = false;

  constructor(
    private serverService: ServerService,
    private authService: AuthService,
    private toast: ToastService,
    private router: Router,
    private loadingController: LoadingController,
    private alertController: AlertController
  ) {
    addIcons({ helpCircleOutline, addCircleOutline, trashOutline });
    this.calculateRecommendedMemory();
  }

  addPort(): void {
    this.additionalPorts.push({
      port: 24454,
      protocol: 'udp',
      host_port: 24454
    });
  }

  removePort(index: number): void {
    this.additionalPorts.splice(index, 1);
  }

  calculateRecommendedMemory(): void {
    // Calcular memoria recomendada según tipo de servidor
    const recommendations: Record<string, { memory_limit_mb: number; java_heap_max_mb: number; java_heap_min_mb: number }> = {
      vanilla: { memory_limit_mb: 2048, java_heap_max_mb: 1536, java_heap_min_mb: 512 },
      paper: { memory_limit_mb: 2048, java_heap_max_mb: 1536, java_heap_min_mb: 512 },
      spigot: { memory_limit_mb: 2048, java_heap_max_mb: 1536, java_heap_min_mb: 512 },
      bukkit: { memory_limit_mb: 2048, java_heap_max_mb: 1536, java_heap_min_mb: 512 },
      fabric: { memory_limit_mb: 4096, java_heap_max_mb: 3584, java_heap_min_mb: 1024 },
      forge: { memory_limit_mb: 4096, java_heap_max_mb: 3584, java_heap_min_mb: 1024 }
    };

    this.recommendedMemory = recommendations[this.serverData.server_type] || recommendations['vanilla'];
    
    // Si no hay memoria configurada, usar recomendada
    if (!this.serverData.memory_limit_mb) {
      this.serverData.memory_limit_mb = this.recommendedMemory.memory_limit_mb;
      this.serverData.java_heap_max_mb = this.recommendedMemory.java_heap_max_mb;
    }
    
    // Calcular jugadores máximos recomendados
    this.calculateMaxPlayers();
  }

  calculateMaxPlayers(): void {
    // Usar memoria configurada o recomendada
    const memoryMB = this.serverData.memory_limit_mb || this.recommendedMemory?.memory_limit_mb || 2048;
    const heapMB = this.serverData.java_heap_max_mb || this.recommendedMemory?.java_heap_max_mb || 1536;
    
    // Fórmula: ~200MB por jugador (base) + memoria base del servidor
    // Memoria base según tipo de servidor
    const baseMemory = {
      vanilla: 512,
      paper: 512,
      spigot: 512,
      bukkit: 512,
      fabric: 1024,
      forge: 1536
    }[this.serverData.server_type] || 512;
    
    // Memoria disponible para jugadores = heap - memoria base
    const availableMemory = heapMB - baseMemory;
    
    // ~200MB por jugador (conservador)
    // ~150MB por jugador (optimista)
    const playersConservative = Math.floor(availableMemory / 200);
    const playersOptimistic = Math.floor(availableMemory / 150);
    
    // Usar el promedio redondeado hacia abajo
    this.maxPlayersRecommended = Math.floor((playersConservative + playersOptimistic) / 2);
    
    // Mínimo 1, máximo 100
    this.maxPlayersRecommended = Math.max(1, Math.min(100, this.maxPlayersRecommended));
    
    // Si el usuario configuró max_players, sugerir actualizarlo
    if (this.serverData.max_players && this.serverData.max_players > this.maxPlayersRecommended) {
      // No forzar, solo informar
    }
  }

  onServerTypeChange(): void {
    this.calculateRecommendedMemory();
  }

  onAutoAssignToggle(): void {
    // Si se desactiva auto-asignación, resetear puertos a valores por defecto
    if (!this.autoAssignPorts) {
      this.serverData.port = 0;
      this.serverData.rcon_port = 0;
    }
  }

  async showMemoryHelp(type: 'total' | 'heap'): Promise<void> {
    const messages = {
      total: {
        header: 'Memoria Total',
        message: `La memoria total es el límite máximo de RAM que el contenedor Docker puede usar.
        
💡 Recomendaciones:
• Vanilla/Paper: 2GB (suficiente para 10-20 jugadores)
• Fabric: 4GB (necesario para mods)
• Forge: 4-6GB (modpacks grandes)

⚠️ Deja siempre 200MB para el sistema operativo.`
      },
      heap: {
        header: 'Heap Máximo de Java',
        message: `El heap máximo es la memoria que Java puede usar para el servidor Minecraft.
        
📊 Regla general:
• Heap Max = Memoria Total - 200MB

💡 Por qué:
• Java necesita memoria para el servidor
• El sistema necesita ~200MB para funcionar
• Si excedes, el contenedor puede crashear

✅ El sistema calculará esto automáticamente si no lo especificas.`
      }
    };

    const alert = await this.alertController.create({
      header: messages[type].header,
      message: messages[type].message,
      buttons: ['Entendido']
    });

    await alert.present();
  }

  isFormValid(): boolean {
    return !!(this.serverData.name && this.serverData.host && this.serverData.rcon_port && this.serverData.rcon_password);
  }

  async createServer(): Promise<void> {
    try {
      // Validación mejorada con mensajes específicos
      if (!this.serverData.name) {
        alert('❌ El nombre del servidor es requerido');
        return;
      }

      if (!this.serverData.host) {
        alert('❌ El host es requerido (IP o nombre del contenedor)');
        return;
      }

      // Validar puertos solo si se especifican manualmente (no auto-asignación)
      if (!this.autoAssignPorts) {
        if (this.serverData.port && (this.serverData.port < 1 || this.serverData.port > 65535)) {
          alert('❌ El puerto de Minecraft debe estar entre 1 y 65535');
          return;
        }
        if (this.serverData.rcon_port && (this.serverData.rcon_port < 1 || this.serverData.rcon_port > 65535)) {
          alert('❌ El puerto RCON debe estar entre 1 y 65535');
          return;
        }
      }

      if (!this.serverData.rcon_password) {
        alert('❌ La contraseña RCON es requerida');
        return;
      }

      // Validar memoria si está configurada
      if (this.serverData.memory_limit_mb && this.serverData.java_heap_max_mb) {
        if (this.serverData.java_heap_max_mb >= this.serverData.memory_limit_mb) {
          alert('❌ El heap máximo debe ser menor que la memoria total (deja 200MB para el sistema)');
          return;
        }
      }

      // Preparar puertos adicionales
      const additionalPorts = this.additionalPorts
        .filter(p => p.port > 0 && p.port <= 65535)
        .map(p => ({
          port: p.port,
          protocol: p.protocol,
          host_port: p.host_port || p.port
        }));

      // Preparar datos para enviar al backend
      const requestData: any = {
        ...this.serverData,
        additional_ports: additionalPorts.length > 0 ? additionalPorts : undefined
      };
      
      // Si auto-asignar puertos está activado, enviar 0 o null para que el backend los asigne
      if (this.autoAssignPorts) {
        requestData.port = null;
        requestData.rcon_port = null;
      } else {
        // Si se especificaron manualmente, usar esos valores (o 0 si están vacíos)
        if (!requestData.port || requestData.port === 0) {
          requestData.port = null;
        }
        if (!requestData.rcon_port || requestData.rcon_port === 0) {
          requestData.rcon_port = null;
        }
      }

      this.isCreating = true;
      this.serverService.createServer(requestData).subscribe({
        next: (response: any) => {
          this.isCreating = false;
          const serverId = response.server_id || response.data?.id || response.id || 1;
          
          // Mostrar puertos asignados si fueron auto-asignados
          let successMessage = `✅ Servidor "${this.serverData.name}" creado correctamente con ID: ${serverId}`;
          if (this.autoAssignPorts && response.data) {
            const assignedPort = response.data.port;
            const assignedRconPort = response.data.rcon_port;
            if (assignedPort || assignedRconPort) {
              successMessage += `\n\nPuertos asignados automáticamente:\n• Minecraft: ${assignedPort || 'N/A'}\n• RCON: ${assignedRconPort || 'N/A'}`;
            }
          }
          
          alert(successMessage);
          this.authService.setCurrentServerId(serverId);
          this.router.navigate(['/dashboard']);
        },
        error: (error) => {
          this.isCreating = false;
          // Mensajes de error más amigables
          let errorMessage = 'Error al crear servidor';
          
          if (error.error?.error) {
            errorMessage = error.error.error;
          } else if (error.status === 400) {
            errorMessage = '❌ Datos inválidos. Verifica que todos los campos sean correctos.';
          } else if (error.status === 403) {
            errorMessage = '❌ No tienes permisos para crear servidores';
          } else if (error.status === 500) {
            errorMessage = '❌ Error del servidor. Intenta de nuevo o contacta al administrador.';
          }
          
          alert(errorMessage);
        }
      });
    } catch (error) {
      alert('Error inesperado: ' + error);
    }
  }
}

