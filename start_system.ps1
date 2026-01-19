# Health System Startup Script
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    Personal Health System Starting..." -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan

# 1. Clean up
Write-Host "`n[1/3] Cleaning up old processes..." -ForegroundColor Magenta
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Start Backend
Write-Host "[2/3] Starting Backend API (Port 8000)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; .venv\Scripts\activate; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Wait for backend
$ready = $false
for ($i = 1; $i -le 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "    ✓ Backend is Ready!" -ForegroundColor Green
        $ready = $true
        break
    } catch {
        Write-Host "    Waiting for backend... ($i/15)" -ForegroundColor Yellow
    }
}

if (-not $ready) {
    Write-Host "`n❌ Backend failed to start! Check the new PowerShell window." -ForegroundColor Red
    pause
    exit 1
}

# 3. Start Streamlit
Write-Host "[3/3] Starting Streamlit UI (Port 8501)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; .venv\Scripts\activate; streamlit run frontend/main.py --server.port 8501"

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "    ✅ Startup Commands Sent!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Service URLs:"
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - Streamlit UI: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the new windows for status." -ForegroundColor Yellow

# Open Browser
Start-Sleep -Seconds 3
Start-Process "http://localhost:8501"
