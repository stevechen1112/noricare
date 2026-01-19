Param(
  [string]$ServerIp = "172.235.200.10",
  [string]$ServerUser = "root",
  [string]$Domain = "noricare.app",
  [string]$RemoteDir = "/root/personalhealth",
  [string]$IdentityFile = "",
  [switch]$SkipFlutterBuild,
  [switch]$SkipHealthCheck
)

$ErrorActionPreference = 'Stop'

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Linode 部署腳本 (2026-01-19 UI 更新版)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "[deploy] Target: $ServerUser@$ServerIp ($Domain)" -ForegroundColor Yellow
Write-Host ""

$sshTarget = "$ServerUser@$ServerIp"
$sshArgs = @()
$scpArgs = @()

if ($IdentityFile -and (Test-Path $IdentityFile)) {
  Write-Host "[deploy] Using SSH identity file: $IdentityFile"
  $sshArgs += @('-i', $IdentityFile, '-o', 'IdentitiesOnly=yes')
  $scpArgs += @('-i', $IdentityFile, '-o', 'IdentitiesOnly=yes')
} elseif ($IdentityFile) {
  throw "IdentityFile not found: $IdentityFile"
}

# 1) Build Flutter web
if (-not $SkipFlutterBuild) {
  Write-Host "[deploy] Step 1/4: Building Flutter web..." -ForegroundColor Green
  Write-Host "  - 包含新 UI 更新: Shimmer loading, Markdown 渲染, 圖片預覽, 滑動刪除" -ForegroundColor Gray
  Set-Location "$PSScriptRoot\..\mobile\flutter_app"
  
  # 檢查 Flutter 是否可用
  $flutterVersion = flutter --version 2>&1 | Select-String "Flutter"
  if ($flutt"
Write-Host "[deploy] Step 2/4: 打包並上傳專案到 Linode..." -ForegroundColor Green
Set-Location "$PSScriptRoot\.."

# Create a local tarball, then scp it up (allows passphrase prompt)
$tempTar = Join-Path $env:TEMP "personalhealth_deploy_$([DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss')).tar.gz"
Write-Host "  - 創建壓縮檔: $tempTar" -ForegroundColor Gray

& tar -czf $tempTar @(
  '--exclude=.venv',
  '--exclude=__pycache__',
  '--exclude=logs',
  '--exclude=uploads',
  '--exclude=ms-playwright',
  '--exclude=sql_app.db',
  '--exclude=steve_personaldata',
  '--exclude=*.log'
) .

$tarSize = (Get-Item $tempTar).Length / 1MB
Write-Host "  - 壓縮檔大小: $([math]::Round($tarSize, 2)) MB" -ForegroundColor Gray

Write-Host "  - 上傳到 server (你可能需要輸入 SSH key passphrase)..." -ForegroundColor Gray
& scp @scpArgs $tempTar "${sshTarget}:/tmp/personalhealth.tar.gz"

Write-Host "  - 在 server 上解壓..." -ForegroundColor Gray
$remoteExtract = "set -e; mkdir -p $RemoteDir; tar -xzf /tmp/personalhealth.tar.gz -C $RemoteDir; rm -f /tmp/personalhealth.tar.gz"
& ssh @sshArgs $sshTarget $remoteExtract
"
Write-Host "[deploy] Step 3/4: 啟動 Docker 服務..." -ForegroundColor Green
$remoteCmd = @(
  "set -e",
  "cd $RemoteDir/deploy",
  "if [ ! -f .env.linode ]; then echo '⚠️  建立新環境設定檔 .env.linode (請稍後編輯)'; cp .env.linode.example .env.linode; fi",
  "echo '  - 重新編譯 Docker image (包含新 API endpoints)'",
  "docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build",
  "echo '  - 服務狀態:'",
  "docker compose --env-file .env.linode -f docker-compose.linode.yml ps"
) -join "; "

& ssh @sshArgs $sshTarget $remoteCmd
Write-Host "  ✓ Docker 服務已啟動" -ForegroundColor Green

# 4) Health check
Write-Host ""
Write-Host "[deploy] Step 4/4: 驗證部署狀態..." -ForegroundColor Green

if (-not $SkipHealthCheck) {
  Start-Sleep -Seconds 5  # 等待服務啟動
  
  Write-Host "  - 檢查 Backend API..." -ForegroundColor Gray
  try {
    $healthCheck = Invoke-WebRequest -Uri "https://$Domain/health" -UseBasicParsing -TimeoutSec 10
    if ($healthCheck.StatusCode -eq 200) {
      Write-Host "  ✓ Backend API 正常: /health 返回 200" -ForegroundColor Green
    }
  } catch {
    Write-Host "  ⚠️  Backend API 健康檢查失敗 (可能仍在啟動中)" -ForegroundColor Yellow
    Write-Host "    請稍後手動檢查: https://$Domain/health" -ForegroundColor Yellow
  }
  
  Write-Host "  - 檢查 Frontend..." -ForegroundColor Gray
  try {
    $frontendCheck = Invoke-WebRequest -Uri "https://$Domain/" -UseBasicParsing -TimeoutSec 10
    if ($frontendCheck.Content -like "*flutter*") {
      Write-Host "  ✓ Frontend 正常: 偵測到 Flutter app" -ForegroundColor Green
    }
  } catch {
    Write-Host "  ⚠️  Frontend 檢查失敗 (可能仍在啟動中)" -ForegroundColor Yellow
  }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  部署完成!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 前端網址: https://$Domain" -ForegroundColor White
Write-Host "🔧 API Docs: https://$Domain/docs" -ForegroundColor White
Write-Host "💚 健康檢查: https://$Domain/health" -ForegroundColor White
Write-Host ""
Write-Host "⚙️  環境設定檔: $RemoteDir/deploy/.env.linode" -ForegroundColor Yellow
Write-Host "   請確認以下設定已填寫:" -ForegroundColor Yellow
Write-Host "   - GEMINI_API_KEY" -ForegroundColor Gray
Write-Host "   - JWT_SECRET_KEY" -ForegroundColor Gray
Write-Host "   - POSTGRES_PASSWORD" -ForegroundColor Gray
Write-Host "   - BACKEND_CORS_ORIGINS (需包含 https://$Domain)" -ForegroundColor Gray
Write-Host ""
Write-Host "📋 更新內容摘要:" -ForegroundColor Cyan
Write-Host "   ✓ Flutter UI 更新 (Shimmer, Markdown, 圖片預覽, 滑動刪除)" -ForegroundColor Gray
Write-Host "   ✓ 新增 API: DELETE /meals/{id}" -ForegroundColor Gray
Write-Host "   ✓ 新增 API: GET /users/me/dashboard" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 詳細部署文件: $PSScriptRoot\..\deploy\LINODE_UPDATE_GUIDE.md" -ForegroundColor White
Write-Host "
& scp @scpArgs $tempTar "${sshTarget}:/tmp/personalhealth.tar.gz"

Write-Host "[deploy] Extracting on server..."
$remoteExtract = "set -e; mkdir -p $RemoteDir; tar -xzf /tmp/personalhealth.tar.gz -C $RemoteDir; rm -f /tmp/personalhealth.tar.gz"
& ssh @sshArgs $sshTarget $remoteExtract

Remove-Item -Force $tempTar -ErrorAction SilentlyContinue

# 3) Remote: ensure env file exists, then start compose
Write-Host "[deploy] Starting docker compose on server..."
$remoteCmd = @(
  "set -e",
  "cd $RemoteDir/deploy",
  "if [ ! -f .env.linode ]; then cp .env.linode.example .env.linode; fi",
  "# Ensure APP_DOMAIN is set (edit deploy/.env.linode as needed)",
  "docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build",
  "docker compose --env-file .env.linode -f docker-compose.linode.yml ps"
) -join "; "

& ssh @sshArgs $sshTarget $remoteCmd

Write-Host "[deploy] Done. Verify: https://$Domain/health"
Write-Host "[deploy] Tip: edit $RemoteDir/deploy/.env.linode to set GEMINI_API_KEY, JWT_SECRET_KEY, POSTGRES_PASSWORD, BACKEND_CORS_ORIGINS."
