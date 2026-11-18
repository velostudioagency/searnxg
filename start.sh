#!/usr/bin/env bash
# SearNXG launcher for macOS and Linux.
# Usage: ./start.sh        (or double-click start.command on macOS)

set -u
cd "$(dirname "$0")" || exit 1
ROOT="$(pwd)"

echo
echo "  SearNXG - web search for humans and models"
echo "  ================================================"
echo

# --- Tool checks -------------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "  Python 3 is not installed. Install it from https://www.python.org/"
  exit 1
fi

if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "  Python 3.10 or newer is required. Found: $("$PY" --version 2>&1)"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "  Node.js / npm is not installed. Get the LTS build from https://nodejs.org/"
  exit 1
fi

# A separate venv avoids clobbering the Windows one in a shared folder.
VENV="$ROOT/.venv-unix"
VPY="$VENV/bin/python"

# --- Find free ports (works on macOS and Linux without extra tools) ----------
find_free_port() {
  "$PY" - "$1" <<'PY'
import socket, sys
port = int(sys.argv[1])
while True:
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", port))
        print(port)
        break
    except OSError:
        port += 1
    finally:
        sock.close()
PY
}

BACKEND_PORT="${BACKEND_PORT:-8010}"
UI_PORT="${UI_PORT:-5174}"
BACKEND_PORT="$(find_free_port "$BACKEND_PORT")"
UI_PORT="$(find_free_port "$UI_PORT")"

# --- Optional local SearXNG engine -------------------------------------------
USE_SEARXNG=0
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "  Docker is available. SearNXG can start a local SearXNG engine."
  echo "  The app works fine without it, so this is your choice."
  printf '  Start the SearXNG engine too? [Y/n]: '
  IFS= read -r answer || true
  case "$answer" in
    n|N|no|NO) USE_SEARXNG=0 ;;
    *) USE_SEARXNG=1 ;;
  esac
  if [ "$USE_SEARXNG" -eq 1 ]; then
    echo
    echo "  Starting SearXNG on http://localhost:8080 ..."
    echo "  First run downloads the engine image, so this can take a few minutes."
    if ! docker compose up -d searxng; then
      echo "  Could not start SearXNG. Continuing with built-in sources."
      USE_SEARXNG=0
    fi
  fi
else
  echo "  Docker not found or not running. Built-in sources will be used."
  echo "  Optional: Docker Desktop (macOS) or Docker Engine (Linux) adds a local search engine."
fi

# --- Python environment ------------------------------------------------------
# A sentinel records a *fully installed* venv, so a half-created one is repaired
# instead of being mistaken for a working setup.
READY="$VENV/.searnxg-ready"

create_venv() {
  if ! "$PY" -m venv "$VENV"; then
    echo
    echo "  Could not create a virtual environment."
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    echo "  Fedora/RHEL:   sudo dnf install python3-pip"
    echo "  macOS:         install Python from python.org or 'brew install python'"
    exit 1
  fi
}

if [ ! -x "$VPY" ]; then
  echo
  echo "  [1/4] Setting up Python. This only happens once..."
  create_venv
elif [ ! -f "$READY" ] && ! "$VPY" -m pip --version >/dev/null 2>&1; then
  echo
  echo "  [1/4] Repairing an incomplete Python environment..."
  rm -rf "$VENV"
  create_venv
fi

if [ -f "$READY" ]; then
  echo
  echo "  [1/4] Python is ready."
else
  echo "  [1/4] Installing backend dependencies..."
  "$VPY" -m pip install --upgrade pip -q || exit 1
  "$VPY" -m pip install -r backend/requirements.txt || exit 1
  touch "$READY"
fi

# --- Frontend ----------------------------------------------------------------
SENTINEL="frontend/node_modules/.searnxg-unix"
if [ ! -f "$SENTINEL" ]; then
  echo "  [2/4] Installing / repairing frontend dependencies..."
  (cd frontend && npm install) || exit 1
  touch "$SENTINEL"
else
  echo "  [2/4] Interface files are ready."
fi

if [ ! -f frontend/dist/index.html ]; then
  echo "  [3/4] Building the interface..."
  (cd frontend && npm run build) || exit 1
else
  echo "  [3/4] Interface is built."
fi

echo "  [4/4] Starting SearNXG..."
echo
echo "  Web page:   http://localhost:$UI_PORT"
echo "  API:        http://localhost:$BACKEND_PORT"
echo "  Engine:     $USE_SEARXNG (0 = built-in sources, 1 = local SearXNG)"
echo "  Help:       http://localhost:$BACKEND_PORT/api/docs"
echo
echo "  Logs: .run/api.log and .run/ui.log"
echo "  Run ./stop.sh to stop both servers."
echo

mkdir -p .run
# Detach fully so the servers survive this script and its terminal closing.
if command -v setsid >/dev/null 2>&1; then
  LAUNCH=setsid
else
  LAUNCH=nohup
fi

if [ "$USE_SEARXNG" -eq 1 ]; then
  $LAUNCH bash -c "cd '$ROOT/backend'; export SEARXNG_URL=http://localhost:8080; exec '$VPY' -m uvicorn app.main:app --host 127.0.0.1 --port '$BACKEND_PORT'" >"$ROOT/.run/api.log" 2>&1 &
else
  $LAUNCH bash -c "cd '$ROOT/backend'; exec '$VPY' -m uvicorn app.main:app --host 127.0.0.1 --port '$BACKEND_PORT'" >"$ROOT/.run/api.log" 2>&1 &
fi
API_PID=$!
disown "$API_PID" 2>/dev/null || true

$LAUNCH bash -c "cd '$ROOT/frontend'; export VITE_BACKEND_PORT='$BACKEND_PORT' VITE_UI_PORT='$UI_PORT'; exec npm run dev" >"$ROOT/.run/ui.log" 2>&1 &
UI_PID=$!
disown "$UI_PID" 2>/dev/null || true

echo "$API_PID $UI_PID" > .run/pids

URL="http://localhost:$UI_PORT"
if command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
fi

echo "  Open $URL in your browser."
