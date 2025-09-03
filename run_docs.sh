#!/usr/bin/env bash
set -euo pipefail

# Build and view documentation.
# Default behavior is to serve with live reload and open the browser.
# Usage:
#   ./run_docs.sh                     # Serve at http://127.0.0.1:8000 (auto-picks free port) and open browser
#   ./run_docs.sh --serve             # Same as default
#   ./run_docs.sh --build             # Build static site and open file:// site
#   ./run_docs.sh --deploy            # Deploy to GitHub Pages (gh-pages) and open URL
#   ./run_docs.sh --serve --no-open   # Serve without opening the browser
#   ./run_docs.sh --serve --port 8080 # Serve on specific port (auto-fallback if busy)
#   ./run_docs.sh --serve --address 0.0.0.0 --strict-port  # Bind strictly and fail if busy
#   DOCS_ADDRESS=0.0.0.0 DOCS_PORT=8080 ./run_docs.sh --serve

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ADDRESS="${DOCS_ADDRESS:-127.0.0.1}"
PORT="${DOCS_PORT:-8000}"
STRICT_PORT=false
# Auto-open browser unless CI or NO_OPEN env is set
if [[ "${CI:-}" == "true" || -n "${NO_OPEN:-}" ]]; then
  AUTO_OPEN=false
else
  AUTO_OPEN=true
fi
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
  if [[ "$AUTO_OPEN" != true ]]; then
    echo "Skipping auto-open. URL: $url"
    return 0
  fi
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

# Check if a TCP port is in use on localhost (best-effort)
is_port_in_use() {
  local port="$1"
  if have_cmd lsof; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1 && return 0 || return 1
  elif have_cmd ss; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -E "(:|\.)$port$" >/dev/null 2>&1 && return 0 || return 1
  elif have_cmd netstat; then
    netstat -ltn 2>/dev/null | awk '{print $4}' | grep -E "(:|\.)$port$" >/dev/null 2>&1 && return 0 || return 1
  else
    return 1
  fi
}

find_free_port() {
  local start_port="$1"
  local max_tries=50
  local candidate="$start_port"
  for _ in $(seq 1 "$max_tries"); do
    if ! is_port_in_use "$candidate"; then
      echo "$candidate"
      return 0
    fi
    candidate=$((candidate + 1))
  done
  echo ""
  return 1
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

# Parse args (supports --port, --address, --no-open, --open, --strict-port)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --serve)
      MODE="serve"; shift ;;
    --build)
      MODE="build"; shift ;;
    --deploy)
      MODE="deploy"; shift ;;
    --port)
      PORT="$2"; shift 2 ;;
    --port=*)
      PORT="${1#*=}"; shift ;;
    --address)
      ADDRESS="$2"; shift 2 ;;
    --address=*)
      ADDRESS="${1#*=}"; shift ;;
    --no-open)
      AUTO_OPEN=false; shift ;;
    --open)
      AUTO_OPEN=true; shift ;;
    --strict-port)
      STRICT_PORT=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--serve|--build|--deploy] [--address ADDR] [--port PORT] [--no-open|--open] [--strict-port]"
      echo "Environment: DOCS_ADDRESS, DOCS_PORT, NO_OPEN=1, CI=true"
      exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--serve|--build|--deploy] [--address ADDR] [--port PORT] [--no-open|--open] [--strict-port]" >&2
      exit 2 ;;
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
  if [[ "$REPO_URL" =~ github.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    RAW_REPO="${BASH_REMATCH[2]}"
    REPO="${RAW_REPO%.git}"
    PAGES_URL="https://${OWNER}.github.io/${REPO}/"
    open_browser "$PAGES_URL"
    echo "Opened: $PAGES_URL"
  else
    echo "Deployed. If using GitHub Pages, enable gh-pages branch in repository settings."
  fi
else
  # Resolve port conflicts unless STRICT_PORT
  if is_port_in_use "$PORT"; then
    if [[ "$STRICT_PORT" == true ]]; then
      echo "Error: Port $PORT is already in use. Use --port to change or omit --strict-port to auto-select." >&2
      exit 1
    fi
    echo "Info: Port $PORT is busy. Searching for a free port..."
    NEW_PORT="$(find_free_port "$PORT")"
    if [[ -z "$NEW_PORT" ]]; then
      echo "Error: Could not find a free port starting from $PORT." >&2
      exit 1
    fi
    echo "Info: Using free port $NEW_PORT instead of $PORT."
    PORT="$NEW_PORT"
  fi

  echo "Serving documentation (dev server)"
  echo "  Address:   $ADDRESS"
  echo "  Port:      $PORT"
  echo "  URL:       http://$ADDRESS:$PORT"
  echo "  Auto-open: $AUTO_OPEN"
  # shellcheck disable=SC2086
  eval "$RUNNER serve -a $ADDRESS:$PORT" | cat &
  SERVER_PID=$!
  # Give server a moment to start
  sleep 2
  open_browser "http://$ADDRESS:$PORT"
  # Wait for server (Ctrl+C to stop)
  trap 'kill $SERVER_PID 2>/dev/null || true' INT TERM EXIT
  wait "$SERVER_PID" || true
  trap - INT TERM EXIT
fi
