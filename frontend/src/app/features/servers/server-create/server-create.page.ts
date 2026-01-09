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
  AlertController
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { helpCircleOutline } from 'ionicons/icons';
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
    IonNote
  ]
})
export class ServerCreatePage {
  serverData: CreateServerRequest & {
    memory_limit_mb?: number;
    java_heap_max_mb?: number;
  } = {
    name: '',
    host: '',
    port: 25565,
    rcon_port: 25575,
    rcon_password: '',
    server_type: 'vanilla',
    version: 'latest',
    max_players: 20,
    difficulty: 'normal',
    pvp_enabled: false,
    whitelist_enabled: true
  };

  recommendedMemory: { memory_limit_mb: number; java_heap_max_mb: number; java_heap_min_mb: number } | null = null;
  maxPlayersRecommended: number = 0;

  constructor(
    private serverService: ServerService,
    private authService: AuthService,
    private toast: ToastService,
    private router: Router,
    private loadingController: LoadingController,
    private alertController: AlertController
  ) {
    addIcons({ helpCircleOutline });
    this.calculateRecommendedMemory();
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
    const isValid = !!(this.serverData.name && this.serverData.host && this.serverData.rcon_port && this.serverData.rcon_password);
    console.log('isFormValid:', isValid, this.serverData);
    return isValid;
  }

  async createServer(): Promise<void> {
    try {
      console.log('createServer called!', this.serverData);
      
      // Validación mejorada con mensajes específicos
      if (!this.serverData.name) {
        console.error('Validation failed: name is required');
        alert('❌ El nombre del servidor es requerido');
        return;
      }

      if (!this.serverData.host) {
        console.error('Validation failed: host is required');
        alert('❌ El host es requerido (IP o nombre del contenedor)');
        return;
      }

      if (!this.serverData.rcon_port || this.serverData.rcon_port < 1 || this.serverData.rcon_port > 65535) {
        console.error('Validation failed: rcon_port is invalid');
        alert('❌ El puerto RCON debe estar entre 1 y 65535');
        return;
      }

      if (!this.serverData.rcon_password) {
        console.error('Validation failed: rcon_password is required');
        alert('❌ La contraseña RCON es requerida');
        return;
      }

      // Validar memoria si está configurada
      if (this.serverData.memory_limit_mb && this.serverData.java_heap_max_mb) {
        if (this.serverData.java_heap_max_mb >= this.serverData.memory_limit_mb) {
          console.error('Validation failed: heap >= memory');
          alert('❌ El heap máximo debe ser menor que la memoria total (deja 200MB para el sistema)');
          return;
        }
      }

      console.log('Validation passed, calling serverService.createServer...');

      this.serverService.createServer(this.serverData).subscribe({
        next: (response: any) => {
          console.log('Server created successfully!', response);
          const serverId = response.server_id || response.data?.id || response.id || 1;
          alert(`✅ Servidor "${this.serverData.name}" creado correctamente con ID: ${serverId}`);
          this.authService.setCurrentServerId(serverId);
          this.router.navigate(['/dashboard']);
        },
        error: (error) => {
          console.error('Error creating server:', error);
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
      console.log('Subscribe set up, waiting for response...');
    } catch (error) {
      console.error('Exception in createServer:', error);
      alert('Error inesperado: ' + error);
    }
  }
}

