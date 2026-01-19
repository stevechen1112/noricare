# 個人健康系統快速啟動腳本
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    個人健康系統啟動中..." -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan

# 激活虛擬環境
& .venv\Scripts\Activate.ps1

# 清理舊進程
Write-Host "`n[1/4] 清理舊進程..." -ForegroundColor Magenta
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 啟動後端 API（獨立視窗）
Write-Host "[2/4] 啟動後端 API (port 8000)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\User\Desktop\personalhealth'; & .venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# 等待後端就緒
Write-Host "[3/4] 等待後端就緒..." -ForegroundColor Magenta
$ready = $false
for ($i = 1; $i -le 10; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "    ✓ 後端已就緒！" -ForegroundColor Green
        $ready = $true
        break
    } catch {
        Write-Host "    等待中... ($i/10)" -ForegroundColor Yellow
    }
}

if (-not $ready) {
    Write-Host "`n❌ 後端啟動失敗！" -ForegroundColor Red
    Write-Host "請檢查後端視窗的錯誤訊息。" -ForegroundColor Yellow
    exit 1
}

# 啟動 Streamlit（獨立視窗）
Write-Host "[4/4] 啟動 Streamlit UI (port 8501)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\User\Desktop\personalhealth'; & .venv\Scripts\Activate.ps1; streamlit run frontend/main.py --server.port 8501 --server.headless true"

Start-Sleep -Seconds 5

# 驗證 Streamlit
Write-Host "`n正在驗證 Streamlit..." -ForegroundColor Magenta
try {
    Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 3 | Out-Null
    Write-Host "✓ Streamlit 已就緒！" -ForegroundColor Green
} catch {
    Write-Host "⚠ Streamlit 可能還在啟動中..." -ForegroundColor Yellow
}

# 完成
Write-Host "`n================================================" -ForegroundColor Green
Write-Host "    ✅ 系統啟動完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "服務地址：" -ForegroundColor Cyan
Write-Host "  🔧 後端 API:   http://localhost:8000" -ForegroundColor White
Write-Host "  🌐 Streamlit:  http://localhost:8501" -ForegroundColor White
Write-Host "  📚 API 文檔:   http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  重要提示：" -ForegroundColor Yellow
Write-Host "  - 請保持此 PowerShell 視窗開啟" -ForegroundColor White
Write-Host "  - 按 Ctrl+C 可停止所有服務" -ForegroundColor White
Write-Host "  - 如需重啟，請關閉視窗後重新執行此腳本" -ForegroundColor White
Write-Host ""

# 打開瀏覽器
Write-Host "正在打開瀏覽器..." -ForegroundColor Magenta
Start-Sleep -Seconds 2
Start-Process "http://localhost:8501"

Write-Host "`n系統已啟動。請查看獨立視窗。" -ForegroundColor Cyan
# 不需要 while 迴圈，因為處理程序已移至獨立視窗

