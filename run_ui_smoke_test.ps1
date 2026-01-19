# Starts Streamlit, waits for the web UI to be ready, runs Playwright UI smoke test, then stops Streamlit.
# Prereqs:
# - Backend API running on http://localhost:8000
# - `python -m playwright install chromium` has been run once

$ErrorActionPreference = "Stop"

$root = "C:\Users\User\Desktop\personalhealth"
$python = "$root\.venv\Scripts\python.exe"

Write-Host "Starting Streamlit..." -ForegroundColor Cyan
$streamlit = Start-Process -FilePath $python -ArgumentList "-m streamlit run $root\frontend\main.py --server.headless true --server.port 8501" -PassThru

try {
    Write-Host "Waiting for http://localhost:8501 ..." -ForegroundColor Cyan
    for ($i = 0; $i -lt 30; $i++) {
        if ((Test-NetConnection -ComputerName "localhost" -Port 8501 -WarningAction SilentlyContinue).TcpTestSucceeded) {
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not (Test-NetConnection -ComputerName "localhost" -Port 8501 -WarningAction SilentlyContinue).TcpTestSucceeded) {
        throw "Streamlit did not become ready on port 8501."
    }

    Write-Host "Running UI smoke test..." -ForegroundColor Cyan
    & $python "$root\ui_smoke_test.py"

    Write-Host "UI smoke test PASSED." -ForegroundColor Green
}
finally {
    if ($streamlit -and -not $streamlit.HasExited) {
        Write-Host "Stopping Streamlit (PID $($streamlit.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $streamlit.Id -Force
    }
}
