#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/ and rerun this script." >&2
  exit 1
fi

cd "$REPO_ROOT"
uv sync --all-extras --dev

echo "Environment setup complete. Use 'uv run' to execute tools." 
