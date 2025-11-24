#!/usr/bin/env bash

# stop_local.sh - Robustly kill backend and frontend processes

echo "[stop] Stopping CoverOCR services..."

# Function to kill process by port
kill_by_port() {
  local port=$1
  local name=$2
  
  # Find PIDs using lsof
  pids=$(lsof -ti :$port 2>/dev/null)
  
  if [ -n "$pids" ]; then
    echo "       Found $name on port $port (PIDs: $(echo $pids | tr '\n' ' ')). Killing..."
    # Kill nicely first
    kill $pids 2>/dev/null || true
    sleep 1
    # Force kill if still alive
    kill -9 $pids 2>/dev/null || true
  else
    echo "       No process found on port $port ($name)."
  fi
}

# 1. Kill by PID files if they exist (fast path)
if [ -f ".backend.pid" ]; then
  pid=$(cat .backend.pid)
  if kill -0 "$pid" 2>/dev/null; then
    echo "       Killing Backend by PID file ($pid)..."
    kill "$pid" 2>/dev/null || true
  fi
  rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
  pid=$(cat .frontend.pid)
  # Note: npm run dev spawns child processes, killing the parent might not be enough,
  # but we try it as a first step.
  if kill -0 "$pid" 2>/dev/null; then
    echo "       Killing Frontend by PID file ($pid)..."
    kill "$pid" 2>/dev/null || true
  fi
  rm .frontend.pid
fi

# 2. Kill by Ports (Robust path)
kill_by_port 8000 "Backend (Uvicorn)"
kill_by_port 5173 "Frontend (Vite)"

# 3. Final cleanup of any lingering python/node processes related to this project
# (Optional, be careful not to kill other projects)
# pkill -f "uvicorn backend.app.main:app" || true

echo "[stop] Done."
