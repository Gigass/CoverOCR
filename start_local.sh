#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] 创建 Python 虚拟环境..."
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [ ! -f "$VENV_DIR/.deps_installed" ]; then
  echo "[setup] 安装后端依赖..."
  pip install --upgrade pip >/dev/null
  pip install -r "$ROOT_DIR/backend/requirements.txt" >/dev/null
  touch "$VENV_DIR/.deps_installed"
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  echo "[setup] 安装前端依赖..."
  (cd "$ROOT_DIR/frontend" && npm install >/dev/null)
fi

cleanup() {
  echo ""
  echo "[shutdown] 停止开发服务器..."
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID"
  fi
  if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID"
  fi
}
trap cleanup EXIT

echo "[start] 启动 FastAPI (http://localhost:8000)..."
(cd "$ROOT_DIR" && uvicorn backend.app.main:app --reload --reload-dir backend) &
BACKEND_PID=$!

echo "[start] 启动 Vite 前端 (http://localhost:5173)..."
(cd "$ROOT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo "[ready] 前后端已启动，按 Ctrl+C 停止。"

wait "$BACKEND_PID" "$FRONTEND_PID"
