#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$SKILL_DIR/templates"

workspace=""
force="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      workspace="${2:-}"
      shift 2
      ;;
    --force)
      force="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$workspace" ]]; then
  echo "Usage: bash scripts/init_workspace.sh --workspace <path> [--force]" >&2
  exit 1
fi

mkdir -p "$workspace"

copy_template() {
  local src="$1"
  local dest="$2"

  if [[ -f "$dest" && "$force" != "true" ]]; then
    echo "reused:$dest"
    return
  fi

  cp "$src" "$dest"
  echo "written:$dest"
}

copy_template "$TEMPLATE_DIR/prd.md" "$workspace/prd.md"
copy_template "$TEMPLATE_DIR/execution-playbook.md" "$workspace/execution-playbook.md"
copy_template "$TEMPLATE_DIR/benchmark.md" "$workspace/benchmark.md"
