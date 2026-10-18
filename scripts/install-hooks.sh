#!/usr/bin/env bash
# =============================================================================
# install-hooks.sh — Instala los git hooks del proyecto en .git/hooks/
# Ejecutar una vez después de clonar: bash scripts/install-hooks.sh
# =============================================================================

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_SRC="$REPO_ROOT/.githooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

if [[ ! -d "$HOOKS_SRC" ]]; then
  echo "Error: no se encontró el directorio .githooks en $REPO_ROOT"
  exit 1
fi

for hook in "$HOOKS_SRC"/*; do
  name=$(basename "$hook")
  dest="$HOOKS_DST/$name"

  cp "$hook" "$dest"
  chmod +x "$dest"
  echo "✓ Hook instalado: $name → $dest"
done

echo ""
echo "Hooks instalados correctamente. El escáner de secretos está activo."
