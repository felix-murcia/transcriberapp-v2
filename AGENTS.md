# Claude AI Agent Configuration

Este proyecto usa agentes de Claude para asistencia.

## Agentes disponibles:
- Usar configuración de ~/.claude/agents/
- Tipos de agentes: code-review, refactor, test, documentation

## Instrucciones para AI:
1. NO crear worktrees sin permiso explícito del usuario
2. NO crear branches temporales automáticamente
3. Para hacer cambios, preguntar primero en qué rama trabajar
4. Usar `git status` antes de cualquier modificación

## Worktree Policy:
- PROHIBIDA la creación automática de worktrees
- Si se necesita un worktree, el usuario lo creará manualmente
- Limpiar worktrees huérfanos: `git worktree prune`
