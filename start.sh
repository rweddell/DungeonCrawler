#!/usr/bin/env bash
# DungeonCrawler — start all components
# Usage: ./start.sh
# Requires: Ollama, uv, Node.js/npm

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDS=()

# ── colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()  { echo -e "${CYAN}  $*${NC}"; }
ok()    { echo -e "${GREEN}  $*${NC}"; }
warn()  { echo -e "${YELLOW}  $*${NC}"; }
error() { echo -e "${RED}  [ERROR] $*${NC}"; exit 1; }

# ── cleanup on exit ───────────────────────────────────────────────────────────
cleanup() {
    echo ""
    warn "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    ok "Stopped."
}
trap cleanup EXIT INT TERM

# ── preflight checks ─────────────────────────────────────────────────────────
echo ""
info "DungeonCrawler — startup"
echo ""

command -v ollama &>/dev/null || error "ollama not found. Install from https://ollama.com"
command -v uv     &>/dev/null || error "uv not found. Install with: pip install uv"
command -v npm    &>/dev/null || error "npm not found. Install Node.js from https://nodejs.org"

# ── install dependencies if needed ───────────────────────────────────────────
if [ ! -d "$ROOT/backend/.venv" ]; then
    info "Installing backend dependencies..."
    (cd "$ROOT/backend" && uv sync)
fi

if [ ! -d "$ROOT/frontend/node_modules" ]; then
    info "Installing frontend dependencies..."
    (cd "$ROOT/frontend" && npm install --silent)
fi

# ── start Ollama ──────────────────────────────────────────────────────────────
info "Checking Ollama..."
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    ok "Ollama already running."
else
    info "Starting Ollama..."
    ollama serve &>/dev/null &
    PIDS+=($!)

    waited=0
    while [ $waited -lt 15 ]; do
        sleep 1; waited=$((waited+1))
        curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 && break
    done
    ok "Ollama ready."
fi

# ── start backend ─────────────────────────────────────────────────────────────
info "Starting backend (port 8000)..."
(
    cd "$ROOT/backend"
    uv run uvicorn app.main:app --reload --port 8000 2>&1 | sed 's/^/  [backend] /'
) &
PIDS+=($!)

waited=0
while [ $waited -lt 20 ]; do
    sleep 1; waited=$((waited+1))
    curl -sf http://localhost:8000/health >/dev/null 2>&1 && break
done
ok "Backend ready."

# ── start frontend ────────────────────────────────────────────────────────────
info "Starting frontend (port 5173)..."
(
    cd "$ROOT/frontend"
    npm run dev 2>&1 | sed 's/^/  [frontend] /'
) &
PIDS+=($!)

# ── open browser ──────────────────────────────────────────────────────────────
sleep 3
info "Opening http://localhost:5173"
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5173
elif command -v open &>/dev/null; then
    open http://localhost:5173
elif command -v start &>/dev/null; then
    start http://localhost:5173
fi

echo ""
ok "All services running. Press Ctrl+C to stop everything."
echo ""
echo -e "  Backend:  http://localhost:8000"
echo -e "  API docs: http://localhost:8000/docs"
echo -e "  Frontend: http://localhost:5173"
echo ""

# Keep alive and stream logs
wait
