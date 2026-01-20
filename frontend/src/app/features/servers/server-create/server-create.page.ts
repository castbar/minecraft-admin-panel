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
import { helpCircleOutline, addCircleOutline, trashOutline, bugOutline } from 'ionicons/icons';
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
    addIcons({ helpCircleOutline, addCircleOutline, trashOutline, bugOutline });
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
    this.onFieldChange();
  }
  
  onFieldChange(): void {
    // Este método se llama cuando cambian los campos
    // Angular debería detectar los cambios automáticamente con ngModel
    // El botón se actualiza automáticamente porque usa [disabled]="!isFormValid()"
  }
  
  debugValidation(): void {
    console.log('=== DEBUG VALIDACIÓN DEL FORMULARIO ===');
    console.log('Estado completo del formulario:', JSON.stringify(this.serverData, null, 2));
    console.log('Auto-asignar puertos:', this.autoAssignPorts);
    console.log('Puertos adicionales:', this.additionalPorts);
    console.log('');
    
    // Validar cada campo individualmente
    const checks: { field: string; valid: boolean; value: any; reason?: string }[] = [];
    
    // Nombre
    const hasName = !!(this.serverData.name && this.serverData.name.trim());
    checks.push({
      field: 'Nombre',
      valid: hasName,
      value: this.serverData.name,
      reason: hasName ? undefined : 'Nombre vacío o solo espacios'
    });
    
    // Host
    const hasHost = !!(this.serverData.host && this.serverData.host.trim());
    checks.push({
      field: 'Host',
      valid: hasHost,
      value: this.serverData.host,
      reason: hasHost ? undefined : 'Host vacío o solo espacios'
    });
    
    // Contraseña RCON
    const hasRconPassword = !!(this.serverData.rcon_password && this.serverData.rcon_password.trim());
    checks.push({
      field: 'Contraseña RCON',
      valid: hasRconPassword,
      value: '***' + (this.serverData.rcon_password ? ' (tiene valor)' : ' (vacío)'),
      reason: hasRconPassword ? undefined : 'Contraseña RCON vacía o solo espacios'
    });
    
    // Puertos (solo si auto-asignar está desactivado)
    if (!this.autoAssignPorts) {
      if (this.serverData.port) {
        const portValid = this.serverData.port >= 1 && this.serverData.port <= 65535;
        checks.push({
          field: 'Puerto Minecraft',
          valid: portValid,
          value: this.serverData.port,
          reason: portValid ? undefined : `Puerto fuera de rango (1-65535): ${this.serverData.port}`
        });
      }
      
      if (this.serverData.rcon_port) {
        const rconPortValid = this.serverData.rcon_port >= 1 && this.serverData.rcon_port <= 65535;
        checks.push({
          field: 'Puerto RCON',
          valid: rconPortValid,
          value: this.serverData.rcon_port,
          reason: rconPortValid ? undefined : `Puerto fuera de rango (1-65535): ${this.serverData.rcon_port}`
        });
      }
    } else {
      checks.push({
        field: 'Puertos',
        valid: true,
        value: 'Auto-asignar activado',
        reason: undefined
      });
    }
    
    // Memoria
    if (this.serverData.memory_limit_mb) {
      const memoryValid = this.serverData.memory_limit_mb >= 1024 && this.serverData.memory_limit_mb <= 16384;
      checks.push({
        field: 'Memoria Total',
        valid: memoryValid,
        value: this.serverData.memory_limit_mb,
        reason: memoryValid ? undefined : `Memoria fuera de rango (1024-16384): ${this.serverData.memory_limit_mb}`
      });
      
      if (this.serverData.java_heap_max_mb) {
        const heapValid = this.serverData.java_heap_max_mb >= 512 && 
                         this.serverData.java_heap_max_mb < this.serverData.memory_limit_mb;
        checks.push({
          field: 'Heap Máximo Java',
          valid: heapValid,
          value: this.serverData.java_heap_max_mb,
          reason: heapValid ? undefined : 
            `Heap inválido: debe ser >= 512 y < ${this.serverData.memory_limit_mb}, actual: ${this.serverData.java_heap_max_mb}`
        });
      }
    }
    
    // Max jugadores
    if (this.serverData.max_players !== undefined && this.serverData.max_players !== null) {
      const maxPlayersValid = this.serverData.max_players >= 1 && this.serverData.max_players <= 100;
      checks.push({
        field: 'Max Jugadores',
        valid: maxPlayersValid,
        value: this.serverData.max_players,
        reason: maxPlayersValid ? undefined : `Max jugadores fuera de rango (1-100): ${this.serverData.max_players}`
      });
    }
    
    // Puertos adicionales
    this.additionalPorts.forEach((port, index) => {
      if (port.port && port.port > 0) {
        const portValid = port.port >= 1 && port.port <= 65535;
        const protocolValid = port.protocol === 'tcp' || port.protocol === 'udp';
        checks.push({
          field: `Puerto Adicional ${index + 1}`,
          valid: portValid && protocolValid,
          value: `${port.port} (${port.protocol})`,
          reason: !portValid ? `Puerto fuera de rango: ${port.port}` : 
                  !protocolValid ? `Protocolo inválido: ${port.protocol}` : undefined
        });
      }
    });
    
    // Mostrar resultados
    console.log('RESULTADOS DE VALIDACIÓN:');
    console.log('========================');
    checks.forEach(check => {
      const icon = check.valid ? '✅' : '❌';
      console.log(`${icon} ${check.field}: ${check.valid ? 'VÁLIDO' : 'INVÁLIDO'}`);
      console.log(`   Valor: ${check.value}`);
      if (check.reason) {
        console.log(`   Razón: ${check.reason}`);
      }
    });
    
    console.log('');
    const allValid = checks.every(c => c.valid);
    const invalidFields = checks.filter(c => !c.valid);
    
    console.log(`RESULTADO FINAL: ${allValid ? '✅ FORMULARIO VÁLIDO' : '❌ FORMULARIO INVÁLIDO'}`);
    if (invalidFields.length > 0) {
      console.log('');
      console.log('CAMPOS QUE INVALIDAN EL FORMULARIO:');
      invalidFields.forEach(field => {
        console.log(`  ❌ ${field.field}: ${field.reason}`);
      });
    }
    
    console.log('');
    console.log('Llamada a isFormValid():', this.isFormValid());
    console.log('===========================================');
    
    // Mostrar también en un alert para fácil visualización
    if (allValid) {
      alert('✅ El formulario es VÁLIDO. El botón debería estar habilitado.\n\nRevisa la consola para más detalles.');
    } else {
      const reasons = invalidFields.map(f => `• ${f.field}: ${f.reason}`).join('\n');
      alert(`❌ El formulario es INVÁLIDO por:\n\n${reasons}\n\nRevisa la consola para más detalles.`);
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
    // Validar campos básicos requeridos (mínimos absolutos)
    const hasName = !!(this.serverData.name && this.serverData.name.trim());
    const hasHost = !!(this.serverData.host && this.serverData.host.trim());
    const hasRconPassword = !!(this.serverData.rcon_password && this.serverData.rcon_password.trim());
    
    // Si faltan campos básicos, no es válido
    if (!hasName || !hasHost || !hasRconPassword) {
      return false;
    }
    
    // Si auto-asignar puertos está activado, no validar puertos
    if (this.autoAssignPorts) {
      // Solo validar campos básicos y opcionales si están configurados
      return this.validateOptionalFields();
    }
    
    // Si auto-asignar está desactivado, los puertos son opcionales pero deben ser válidos si se especifican
    if (this.serverData.port && (this.serverData.port < 1 || this.serverData.port > 65535)) {
      return false;
    }
    if (this.serverData.rcon_port && (this.serverData.rcon_port < 1 || this.serverData.rcon_port > 65535)) {
      return false;
    }
    
    return this.validateOptionalFields();
  }
  
  validateOptionalFields(): boolean {
    // Validar memoria si está configurada (opcional)
    if (this.serverData.memory_limit_mb) {
      if (this.serverData.memory_limit_mb < 1024 || this.serverData.memory_limit_mb > 16384) {
        return false;
      }
      
      if (this.serverData.java_heap_max_mb) {
        if (this.serverData.java_heap_max_mb < 512 || this.serverData.java_heap_max_mb >= this.serverData.memory_limit_mb) {
          return false;
        }
      }
    }
    
    // Validar max jugadores (debe estar en rango válido si se especifica)
    if (this.serverData.max_players !== undefined && this.serverData.max_players !== null) {
      if (this.serverData.max_players < 1 || this.serverData.max_players > 100) {
        return false;
      }
    }
    
    // Validar puertos adicionales - solo validar si tienen un valor
    // Si un puerto está vacío (0 o null), se ignora
    for (const port of this.additionalPorts) {
      // Solo validar si el puerto tiene un valor
      if (port.port && port.port > 0) {
        if (port.port < 1 || port.port > 65535) {
          return false;
        }
        if (!port.protocol || (port.protocol !== 'tcp' && port.protocol !== 'udp')) {
          return false;
        }
      }
    }
    
    return true;
  }

  async createServer(): Promise<void> {
    try {
      // Validar que el formulario sea válido antes de proceder
      if (!this.isFormValid()) {
        this.toast.error('Por favor completa todos los campos requeridos correctamente');
        return;
      }

      // Validación mejorada con mensajes específicos
      if (!this.serverData.name || !this.serverData.name.trim()) {
        this.toast.error('El nombre del servidor es requerido');
        return;
      }

      if (!this.serverData.host || !this.serverData.host.trim()) {
        this.toast.error('El host es requerido (IP o nombre del contenedor)');
        return;
      }

      // Validar puertos solo si se especifican manualmente (no auto-asignación)
      if (!this.autoAssignPorts) {
        if (this.serverData.port && (this.serverData.port < 1 || this.serverData.port > 65535)) {
          this.toast.error('El puerto de Minecraft debe estar entre 1 y 65535');
          return;
        }
        if (this.serverData.rcon_port && (this.serverData.rcon_port < 1 || this.serverData.rcon_port > 65535)) {
          this.toast.error('El puerto RCON debe estar entre 1 y 65535');
          return;
        }
      }

      if (!this.serverData.rcon_password || !this.serverData.rcon_password.trim()) {
        this.toast.error('La contraseña RCON es requerida');
        return;
      }

      // Validar memoria si está configurada
      if (this.serverData.memory_limit_mb && this.serverData.java_heap_max_mb) {
        if (this.serverData.java_heap_max_mb >= this.serverData.memory_limit_mb) {
          this.toast.error('El heap máximo debe ser menor que la memoria total (deja 200MB para el sistema)');
          return;
        }
      }
      
      // Validar max jugadores
      if (this.serverData.max_players && (this.serverData.max_players < 1 || this.serverData.max_players > 100)) {
        this.toast.error('El número máximo de jugadores debe estar entre 1 y 100');
        return;
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
          
          this.toast.success(successMessage);
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
            errorMessage = 'Datos inválidos. Verifica que todos los campos sean correctos.';
          } else if (error.status === 403) {
            errorMessage = 'No tienes permisos para crear servidores';
          } else if (error.status === 500) {
            errorMessage = 'Error del servidor. Intenta de nuevo o contacta al administrador.';
          }
          
          this.toast.error(errorMessage);
        }
      });
    } catch (error: any) {
      this.toast.error('Error inesperado: ' + (error?.message || error));
    }
  }
}

