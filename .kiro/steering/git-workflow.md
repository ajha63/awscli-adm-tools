---
inclusion: always
---

# Flujo de trabajo Git — Reglas obligatorias

## Antes de iniciar cualquier tarea

**Siempre** ejecutar los siguientes pasos en orden. No iniciar trabajo nuevo sin completarlos.

### 1. Verificar el estado del repositorio local

```bash
git status
git log --oneline -5
```

Revisar:
- ¿Hay cambios sin commitear (`modified`, `untracked`)?
- ¿Hay commits locales que no se han subido al remoto (`ahead of origin`)?
- ¿La rama activa es la correcta para esta tarea?

### 2. Sincronizar con el repositorio remoto

```bash
git fetch origin
git status          # verifica si hay cambios pendientes de pull
git pull --rebase   # o git merge, según la política del equipo
```

> Si hay cambios locales sin commitear, hacer stash o commitearlos **antes** de hacer pull.

### 3. Resolver pendientes antes de empezar

Si `git status` muestra archivos modificados o sin trackear:

- **Commitear** los cambios listos: `git add <archivos> && git commit -m "mensaje"`
- **Hacer stash** de trabajo en progreso: `git stash push -m "wip: descripción"`
- **Nunca** dejar cambios flotantes al cambiar de contexto o de rama.

---

## Regla para Kiro

Cuando el usuario pide iniciar una tarea nueva:

1. Antes de escribir cualquier código, mostrar el estado actual del repo:
   ```
   git status && git log --oneline -5
   ```
2. Si hay cambios sin commitear o commits sin pushear, **notificar al desarrollador** y pedir que los resuelva antes de continuar.
3. Solo proceder con la nueva tarea cuando el árbol de trabajo esté limpio o el desarrollador confirme explícitamente que quiere continuar de todas formas.

### Mensaje estándar de advertencia

Si hay pendientes, mostrar:

```
⚠️  PENDIENTES EN EL REPOSITORIO
────────────────────────────────────────
Se detectaron cambios sin commitear o commits locales sin subir al remoto.

Antes de iniciar la nueva tarea:
  1. Commitea o haz stash de los cambios actuales.
  2. Sube los commits pendientes: git push
  3. Confirma con: git status  (debe mostrar "nothing to commit")

¿Deseas continuar de todas formas? (los cambios actuales quedarán mezclados con la nueva tarea)
```

---

## Convención de mensajes de commit

Usar [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<alcance>): <descripción corta>

[cuerpo opcional]
```

| Tipo | Cuándo usarlo |
|------|--------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `chore` | Mantenimiento, dependencias |
| `docs` | Solo documentación |
| `refactor` | Refactor sin cambio de comportamiento |
| `test` | Agregar o corregir tests |
| `security` | Cambios de seguridad |

Ejemplos:
```
feat(ec2): agregar listado de instancias por tag
fix(s3): corregir paginación en list_buckets
security(hooks): agregar escaneo de tokens GitHub al pre-commit
```
