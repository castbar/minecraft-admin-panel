# Plugin Fabric para Autenticación con Panel

## 📋 Descripción

Este documento describe cómo crear un mod de Fabric que integre la autenticación del servidor Minecraft con el panel Django.

## 🏗️ Estructura del Proyecto

```
panel-auth-fabric/
├── src/main/java/com/castbar/panelauth/
│   ├── PanelAuthMod.java          # Clase principal del mod
│   ├── AuthManager.java           # Gestor de autenticación
│   ├── PanelAPI.java              # Cliente HTTP para el panel
│   └── LoginScreen.java           # Pantalla de login (opcional)
├── src/main/resources/
│   └── fabric.mod.json            # Configuración del mod
└── build.gradle                   # Dependencias
```

## 📝 Implementación Básica

### 1. fabric.mod.json

```json
{
  "schemaVersion": 1,
  "id": "panel-auth",
  "version": "1.0.0",
  "name": "Panel Auth",
  "description": "Autenticación con panel Django",
  "authors": ["Castbar"],
  "entrypoints": {
    "main": ["com.castbar.panelauth.PanelAuthMod"]
  },
  "depends": {
    "fabricloader": ">=0.14.0",
    "minecraft": "~1.20.1"
  }
}
```

### 2. PanelAuthMod.java

```java
package com.castbar.panelauth;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

public class PanelAuthMod implements ModInitializer {
    private static AuthManager authManager;
    
    @Override
    public void onInitialize() {
        // Configuración desde archivo o variables de entorno
        String panelUrl = System.getenv("PANEL_URL") != null 
            ? System.getenv("PANEL_URL") 
            : "http://localhost:8000";
        String apiKey = System.getenv("PANEL_API_KEY");
        int serverId = Integer.parseInt(System.getenv("PANEL_SERVER_ID") != null 
            ? System.getenv("PANEL_SERVER_ID") 
            : "1");
        
        authManager = new AuthManager(panelUrl, apiKey, serverId);
        
        // Interceptar conexiones
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            String username = player.getName().getString();
            
            // Verificar si el servidor usa autenticación por base de datos
            if (authManager.requiresAuth()) {
                // Solicitar login
                player.sendMessage(Text.of("§c[Panel Auth] Por favor, ingresa tu contraseña: /login <password>"), false);
                
                // Marcar como no autenticado
                authManager.markUnauthenticated(player);
            }
        });
        
        // Registrar comando de login
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            dispatcher.register(CommandManager.literal("login")
                .then(CommandManager.argument("password", StringArgumentType.string())
                    .executes(context -> {
                        ServerPlayerEntity player = context.getSource().getPlayerOrThrow();
                        String password = StringArgumentType.getString(context, "password");
                        
                        if (authManager.authenticate(player, password)) {
                            player.sendMessage(Text.of("§a[Panel Auth] ¡Autenticación exitosa!"), false);
                            return 1;
                        } else {
                            player.sendMessage(Text.of("§c[Panel Auth] Contraseña incorrecta"), false);
                            // Expulsar después de X intentos fallidos
                            return 0;
                        }
                    })
                )
            );
        });
    }
}
```

### 3. AuthManager.java

```java
package com.castbar.panelauth;

import net.minecraft.server.network.ServerPlayerEntity;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

public class AuthManager {
    private final PanelAPI panelAPI;
    private final Map<ServerPlayerEntity, Boolean> authenticatedPlayers = new HashMap<>();
    private final Map<ServerPlayerEntity, Integer> failedAttempts = new HashMap<>();
    private static final int MAX_ATTEMPTS = 3;
    
    public AuthManager(String panelUrl, String apiKey, int serverId) {
        this.panelAPI = new PanelAPI(panelUrl, apiKey, serverId);
    }
    
    public boolean requiresAuth() {
        // Verificar modo de autenticación del servidor
        // Por ahora, siempre requerir si está configurado
        return true;
    }
    
    public boolean authenticate(ServerPlayerEntity player, String password) {
        String username = player.getName().getString();
        
        // Validar contra el panel
        CompletableFuture<Boolean> future = panelAPI.authenticate(username, password);
        
        try {
            Boolean isValid = future.get(); // Bloquear hasta obtener respuesta
            
            if (isValid) {
                authenticatedPlayers.put(player, true);
                failedAttempts.remove(player);
                return true;
            } else {
                int attempts = failedAttempts.getOrDefault(player, 0) + 1;
                failedAttempts.put(player, attempts);
                
                if (attempts >= MAX_ATTEMPTS) {
                    // Expulsar jugador
                    player.networkHandler.disconnect(Text.of("Demasiados intentos fallidos"));
                }
                return false;
            }
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }
    
    public boolean isAuthenticated(ServerPlayerEntity player) {
        return authenticatedPlayers.getOrDefault(player, false);
    }
    
    public void markUnauthenticated(ServerPlayerEntity player) {
        authenticatedPlayers.put(player, false);
    }
}
```

### 4. PanelAPI.java

```java
package com.castbar.panelauth;

import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;

public class PanelAPI {
    private final String panelUrl;
    private final String apiKey;
    private final int serverId;
    private final HttpClient httpClient;
    
    public PanelAPI(String panelUrl, String apiKey, int serverId) {
        this.panelUrl = panelUrl;
        this.apiKey = apiKey;
        this.serverId = serverId;
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    }
    
    public CompletableFuture<Boolean> authenticate(String username, String password) {
        String url = panelUrl + "/api/servers/" + serverId + "/auth/";
        String jsonBody = String.format(
            "{\"username\":\"%s\",\"password\":\"%s\"}",
            username, password
        );
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .header("X-API-Key", apiKey)
            .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
            .timeout(Duration.ofSeconds(5))
            .build();
        
        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
            .thenApply(response -> {
                if (response.statusCode() == 200) {
                    String body = response.body();
                    // Parsear JSON: {"valid": true, ...}
                    return body.contains("\"valid\":true");
                }
                return false;
            })
            .exceptionally(e -> {
                e.printStackTrace();
                return false;
            });
    }
}
```

## ⚙️ Configuración

### Variables de Entorno

El mod lee las siguientes variables de entorno:

- `PANEL_URL`: URL del panel (ej: `http://100.77.240.103:8000`)
- `PANEL_API_KEY`: API key del servidor (obtenida del panel)
- `PANEL_SERVER_ID`: ID del servidor en el panel

### Archivo de Configuración (Alternativa)

Crear `config/panel-auth.properties`:

```properties
panel.url=http://100.77.240.103:8000
panel.api_key=tu_api_key_aqui
panel.server_id=1
panel.timeout=5
panel.max_attempts=3
```

## 🚀 Instalación

1. **Compilar el mod**:
   ```bash
   ./gradlew build
   ```

2. **Copiar JAR al servidor**:
   ```bash
   cp build/libs/panel-auth-1.0.0.jar /ruta/al/servidor/mods/
   ```

3. **Configurar variables de entorno** en el contenedor Docker:
   ```yaml
   environment:
     - PANEL_URL=http://panel-url:8000
     - PANEL_API_KEY=api_key_del_servidor
     - PANEL_SERVER_ID=1
   ```

4. **Reiniciar el servidor**

## 🔄 Flujo de Autenticación

1. Jugador se conecta al servidor
2. Mod intercepta la conexión
3. Mod solicita contraseña (mensaje en chat)
4. Jugador ejecuta `/login <password>`
5. Mod valida contra el panel vía HTTP
6. Si es válido: permite acceso completo
7. Si no es válido: expulsa después de X intentos

## 🛡️ Seguridad

- ✅ Validación de API key
- ✅ Timeout en peticiones HTTP
- ✅ Límite de intentos fallidos
- ✅ Expulsión automática
- ⚠️ **Usar HTTPS en producción**

## 📝 Notas

- Este es un ejemplo básico que necesita mejoras
- Considerar usar un sistema de sesiones para evitar re-autenticación
- Implementar GUI de login (opcional pero mejor UX)
- Agregar soporte para recuperación de contraseña
