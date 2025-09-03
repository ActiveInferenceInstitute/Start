#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

command -v uv >/dev/null 2>&1 || {
  echo "Installing uv...";
  curl -LsSf https://astral.sh/uv/install.sh | sh;
  export PATH="$HOME/.cargo/bin:$PATH";
}

cd "$REPO_ROOT"
uv sync --all-extras --dev

echo "Environment setup complete. Use 'uv run' to execute tools." 

