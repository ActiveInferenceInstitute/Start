#!/usr/bin/env bash
set -euo pipefail

# Build and view documentation.
# Default behavior is to serve with live reload and open the browser.
# Usage:
#   ./run_docs.sh           # Serve at http://127.0.0.1:8000 and open browser
#   ./run_docs.sh --build   # Build static site and open file:// site
#   ./run_docs.sh --deploy  # Deploy to GitHub Pages (gh-pages) and open URL
#   DOCS_ADDRESS=0.0.0.0 DOCS_PORT=8080 ./run_docs.sh --serve

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ADDRESS="${DOCS_ADDRESS:-127.0.0.1}"
PORT="${DOCS_PORT:-8000}"
MODE="serve"  # serve | build | deploy

if [[ -f "$SCRIPT_DIR/mkdocs.yml" ]]; then
  :
else
  echo "Error: mkdocs.yml not found in repo root: $SCRIPT_DIR" >&2
  exit 1
fi

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

open_browser() {
  local url="$1"
  if [[ "${OSTYPE:-}" == darwin* ]]; then
    open "$url" >/dev/null 2>&1 || true
  elif have_cmd xdg-open; then
    xdg-open "$url" >/dev/null 2>&1 || true
  elif have_cmd gnome-open; then
    gnome-open "$url" >/dev/null 2>&1 || true
  else
    echo "Open this URL in your browser: $url"
  fi
}

# Select mkdocs runner without requiring pip inside uv venvs.
select_runner() {
  if have_cmd uvx; then
    echo "uvx mkdocs"
    return 0
  fi
  if have_cmd mkdocs; then
    echo "mkdocs"
    return 0
  fi
  if have_cmd uv; then
    # Use ephemeral packages with uv run
    echo "uv run --with mkdocs --with mkdocs-material mkdocs"
    return 0
  fi
  echo ""  # no runner
}

# Parse args
for arg in "$@"; do
  case "$arg" in
    --serve)
      MODE="serve"
      ;;
    --build)
      MODE="build"
      ;;
    --deploy)
      MODE="deploy"
      ;;
    -h|--help)
      echo "Usage: $0 [--serve|--build|--deploy]"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: $0 [--serve|--build|--deploy]" >&2
      exit 2
      ;;
  esac
done

RUNNER="$(select_runner)"
if [[ -z "$RUNNER" ]]; then
  echo "Error: mkdocs is not available (uvx/mkdocs/uv missing). Install uv (recommended) or mkdocs." >&2
  exit 1
fi

if [[ "$MODE" == "build" ]]; then
  echo "Building documentation ($RUNNER build)..."
  eval "$RUNNER build"
  open_browser "file://$SCRIPT_DIR/site/index.html"
elif [[ "$MODE" == "deploy" ]]; then
  echo "Deploying documentation to GitHub Pages ($RUNNER gh-deploy --force)..."
  eval "$RUNNER gh-deploy --force"
  # Attempt to construct docs URL
  REPO_URL="$(git config --get remote.origin.url || true)"
  if [[ "$REPO_URL" =~ github.com[:/](.+)/(.+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    PAGES_URL="https://${OWNER}.github.io/${REPO}/"
    open_browser "$PAGES_URL"
    echo "Opened: $PAGES_URL"
  else
    echo "Deployed. If using GitHub Pages, enable gh-pages branch in repository settings."
  fi
else
  echo "Serving documentation at http://$ADDRESS:$PORT ..."
  # shellcheck disable=SC2086
  eval "$RUNNER serve -a $ADDRESS:$PORT" | cat &
  SERVER_PID=$!
  # Give server a moment to start
  sleep 2
  open_browser "http://$ADDRESS:$PORT"
  # Wait for server (Ctrl+C to stop)
  wait "$SERVER_PID" || true
fi
