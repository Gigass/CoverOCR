#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

# --- Helper Functions ---
check_port() {
  lsof -i ":$1" >/dev/null 2>&1
}

# --- 1. Environment Setup ---
if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [ ! -f "$VENV_DIR/.deps_installed" ]; then
  echo "[setup] Installing backend dependencies..."
  pip install --upgrade pip >/dev/null
  pip install -r "$ROOT_DIR/backend/requirements.txt" >/dev/null
  touch "$VENV_DIR/.deps_installed"
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  echo "[setup] Installing frontend dependencies..."
  (cd "$ROOT_DIR/frontend" && npm install >/dev/null)
fi

# --- 2. Check Ports ---
if check_port 8000; then
  echo "[warning] Port 8000 is already in use. Attempting to clean up..."
  ./stop_local.sh || true
  sleep 1
fi

if check_port 5173; then
  echo "[warning] Port 5173 is already in use. Attempting to clean up..."
  ./stop_local.sh || true
  sleep 1
fi

# --- 3. Start Services ---

echo "[start] Starting FastAPI (http://localhost:8000)..."
# Run uvicorn directly to avoid shell wrapper issues, and save PID
(cd "$ROOT_DIR" && uvicorn backend.app.main:app --reload --reload-dir backend --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!
echo $BACKEND_PID > "$ROOT_DIR/.backend.pid"

echo "[start] Starting Vite Frontend (http://localhost:5173)..."
(cd "$ROOT_DIR/frontend" && npm run dev -- --host) &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$ROOT_DIR/.frontend.pid"

# --- 4. Cleanup Handler ---
cleanup() {
  echo ""
  echo "[shutdown] Stopping services..."
  
  # Run the stop script to ensure everything is killed properly
  if [ -f "$ROOT_DIR/stop_local.sh" ]; then
    "$ROOT_DIR/stop_local.sh"
  else
    # Fallback if stop script is missing
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "[ready] Services are running."
echo "        Backend:  http://localhost:8000/docs"
echo "        Frontend: http://localhost:5173"
echo "        Press Ctrl+C to stop."

wait "$BACKEND_PID" "$FRONTEND_PID"
