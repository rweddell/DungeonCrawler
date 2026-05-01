# DungeonCrawler — start all components
# Usage: .\start.ps1
# Requires: Ollama, uv, Node.js/npm

$Root = $PSScriptRoot

# ── helpers ──────────────────────────────────────────────────────────────────

function Write-Header([string]$msg) {
    Write-Host ""
    Write-Host "  $msg" -ForegroundColor Cyan
}

function Find-Command([string]$cmd) {
    return $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

# ── preflight checks ─────────────────────────────────────────────────────────

Write-Header "DungeonCrawler — startup"

if (-not (Find-Command "ollama")) {
    Write-Host "  [ERROR] ollama not found. Install from https://ollama.com" -ForegroundColor Red
    exit 1
}
if (-not (Find-Command "uv")) {
    Write-Host "  [ERROR] uv not found. Install with: pip install uv" -ForegroundColor Red
    exit 1
}
if (-not (Find-Command "npm")) {
    Write-Host "  [ERROR] npm not found. Install Node.js from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# ── install dependencies if needed ───────────────────────────────────────────

$BackendVenv = Join-Path $Root "backend\.venv"
if (-not (Test-Path $BackendVenv)) {
    Write-Header "Installing backend dependencies..."
    Push-Location "$Root\backend"
    uv sync
    Pop-Location
}

$NodeModules = Join-Path $Root "frontend\node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Header "Installing frontend dependencies..."
    Push-Location "$Root\frontend"
    npm install --silent
    Pop-Location
}

# ── start Ollama ──────────────────────────────────────────────────────────────

Write-Header "Starting Ollama..."

$ollamaRunning = $false
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) { $ollamaRunning = $true }
} catch {}

if ($ollamaRunning) {
    Write-Host "  Ollama already running." -ForegroundColor Green
} else {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Write-Host "  Waiting for Ollama..." -ForegroundColor Yellow
    $waited = 0
    while ($waited -lt 15) {
        Start-Sleep -Seconds 1
        $waited++
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 1 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { break }
        } catch {}
    }
    Write-Host "  Ollama ready." -ForegroundColor Green
}

# ── start backend ─────────────────────────────────────────────────────────────

Write-Header "Starting backend (port 8000)..."

$backendArgs = @(
    "-NoExit",
    "-Command",
    "Set-Location '$Root\backend'; Write-Host 'Backend starting...' -ForegroundColor Cyan; uv run uvicorn app.main:app --reload --port 8000"
)
Start-Process "powershell" -ArgumentList $backendArgs

# Wait for backend to be reachable
Write-Host "  Waiting for backend..." -ForegroundColor Yellow
$waited = 0
while ($waited -lt 20) {
    Start-Sleep -Seconds 1
    $waited++
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 1 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { break }
    } catch {}
}
Write-Host "  Backend ready." -ForegroundColor Green

# ── start frontend ────────────────────────────────────────────────────────────

Write-Header "Starting frontend (port 5173)..."

$frontendArgs = @(
    "-NoExit",
    "-Command",
    "Set-Location '$Root\frontend'; Write-Host 'Frontend starting...' -ForegroundColor Cyan; npm run dev"
)
Start-Process "powershell" -ArgumentList $frontendArgs

# ── open browser ──────────────────────────────────────────────────────────────

Start-Sleep -Seconds 3
Write-Header "Opening browser at http://localhost:5173"
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "  All services started. Close this window to leave them running." -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor DarkGray
Write-Host "  API docs: http://localhost:8000/docs" -ForegroundColor DarkGray
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor DarkGray
Write-Host ""
