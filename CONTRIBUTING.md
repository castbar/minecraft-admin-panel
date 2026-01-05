# Guía de Contribución

¡Gracias por tu interés en contribuir al Minecraft Admin Panel! 🎮

## 🚀 Cómo Contribuir

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone git@github.com:TU_USUARIO/minecraft-admin-panel.git
cd minecraft-admin-panel
```

### 2. Crear Branch

```bash
# Siempre desde develop
git checkout develop
git pull origin develop

# Crear tu branch
git checkout -b feature/mi-nueva-funcionalidad
# O para fixes:
git checkout -b fix/correccion-de-bug
```

### 3. Desarrollo Local

```bash
# Usar el script helper
./scripts/dev-local.sh

# O seguir la guía en docs/DESARROLLO_LOCAL.md
```

### 4. Hacer Cambios

- ✅ Escribe código limpio y comentado
- ✅ Sigue las convenciones del proyecto
- ✅ Agrega tests si es posible
- ✅ Actualiza documentación si es necesario

### 5. Commit

```bash
git add .
git commit -m "feat: agregar nueva funcionalidad X"
# O
git commit -m "fix: corregir bug en Y"
```

**Convenciones de commits:**
- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formato, punto y coma, etc.
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento

### 6. Push y PR

```bash
git push origin feature/mi-nueva-funcionalidad
```

Luego crea un Pull Request desde tu fork hacia `develop` del repositorio principal.

## 📋 Checklist de PR

Antes de crear un PR, verifica:

- [ ] El código compila sin errores
- [ ] Los tests pasan (si aplica)
- [ ] No hay información sensible (passwords, keys, etc.)
- [ ] La documentación está actualizada
- [ ] El código sigue las convenciones del proyecto
- [ ] Los commits tienen mensajes descriptivos

## 🔍 Code Review

Todas las PRs requieren:
- ✅ Al menos 1 aprobación
- ✅ Que los checks de CI pasen
- ✅ Sin conflictos con `develop`

## 🐛 Reportar Bugs

Si encuentras un bug:

1. Verifica que no esté ya reportado en Issues
2. Crea un nuevo Issue con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Versión y entorno

## 💡 Sugerir Funcionalidades

Para sugerir nuevas funcionalidades:

1. Crea un Issue con la etiqueta `enhancement`
2. Describe la funcionalidad propuesta
3. Explica el caso de uso
4. Espera feedback antes de implementar

## 🔒 Seguridad

**IMPORTANTE:** Si encuentras una vulnerabilidad de seguridad:

- ❌ NO crear un Issue público
- ✅ Contactar directamente: security@castbar.dev
- ✅ Esperar respuesta antes de hacer público

## 📚 Recursos

- [Guía de Desarrollo Local](docs/DESARROLLO_LOCAL.md)
- [Arquitectura del Proyecto](docs/)
- [API Documentation](docs/)

## ❓ Preguntas

Si tienes preguntas:
- Abre un Issue con la etiqueta `question`
- O contacta a los maintainers

¡Gracias por contribuir! 🎉







