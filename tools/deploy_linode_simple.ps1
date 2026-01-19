Param(
  [string]$ServerIp = "172.235.200.10",
  [string]$ServerUser = "root",
  [string]$Domain = "noricare.app",
  [string]$RemoteDir = "/root/personalhealth",
  [string]$IdentityFile = "",
  [switch]$SkipFlutterBuild
)

$ErrorActionPreference = 'Stop'

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Linode Deployment Script" -ForegroundColor Cyan
Write-Host "  Target: $ServerUser@$ServerIp ($Domain)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$sshTarget = "$ServerUser@$ServerIp"
$sshArgs = @()
$scpArgs = @()

if ($IdentityFile -and (Test-Path $IdentityFile)) {
  Write-Host "[INFO] Using SSH identity file: $IdentityFile"
  $sshArgs += @('-i', $IdentityFile, '-o', 'IdentitiesOnly=yes')
  $scpArgs += @('-i', $IdentityFile, '-o', 'IdentitiesOnly=yes')
} elseif ($IdentityFile) {
  throw "IdentityFile not found: $IdentityFile"
}

# Step 1: Build Flutter web (if needed)
if (-not $SkipFlutterBuild) {
  Write-Host "[STEP 1/4] Building Flutter web..." -ForegroundColor Green
  Set-Location "$PSScriptRoot\..\mobile\flutter_app"
  flutter build web --release
  Write-Host "  > Flutter build completed" -ForegroundColor Gray
} else {
  Write-Host "[STEP 1/4] Skipping Flutter build (using existing)" -ForegroundColor Yellow
}

# Step 2: Create archive and upload
Write-Host ""
Write-Host "[STEP 2/4] Creating project archive..." -ForegroundColor Green
Set-Location "$PSScriptRoot\.."

$tempTar = Join-Path $env:TEMP "personalhealth_deploy_$([DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss')).tar.gz"
Write-Host "  > Archive: $tempTar" -ForegroundColor Gray

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
Write-Host "  > Size: $([math]::Round($tarSize, 2)) MB" -ForegroundColor Gray

Write-Host "  > Uploading to server..." -ForegroundColor Gray
& scp @scpArgs $tempTar "${sshTarget}:/tmp/personalhealth.tar.gz"

Write-Host "  > Extracting on server..." -ForegroundColor Gray
$remoteExtract = "set -e; mkdir -p $RemoteDir; tar -xzf /tmp/personalhealth.tar.gz -C $RemoteDir; rm -f /tmp/personalhealth.tar.gz"
& ssh @sshArgs $sshTarget $remoteExtract

Remove-Item -Force $tempTar -ErrorAction SilentlyContinue
Write-Host "  > Upload completed" -ForegroundColor Green

# Step 3: Start Docker services
Write-Host ""
Write-Host "[STEP 3/4] Starting Docker services..." -ForegroundColor Green
$remoteCmd = @(
  "set -e",
  "cd $RemoteDir/deploy",
  "if [ ! -f .env.linode ]; then echo 'Creating .env.linode from example'; cp .env.linode.example .env.linode; fi",
  "docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build",
  "docker compose --env-file .env.linode -f docker-compose.linode.yml ps"
) -join "; "

& ssh @sshArgs $sshTarget $remoteCmd
Write-Host "  > Docker services started" -ForegroundColor Green

# Step 4: Verify deployment
Write-Host ""
Write-Host "[STEP 4/4] Verifying deployment..." -ForegroundColor Green

Start-Sleep -Seconds 5

try {
  $healthCheck = Invoke-WebRequest -Uri "https://$Domain/health" -UseBasicParsing -TimeoutSec 10
  if ($healthCheck.StatusCode -eq 200) {
    Write-Host "  > Backend API: OK" -ForegroundColor Green
  }
} catch {
  Write-Host "  > Backend API: Check manually (may still be starting)" -ForegroundColor Yellow
}

try {
  $frontendCheck = Invoke-WebRequest -Uri "https://$Domain/" -UseBasicParsing -TimeoutSec 10
  if ($frontendCheck.StatusCode -eq 200) {
    Write-Host "  > Frontend: OK" -ForegroundColor Green
  }
} catch {
  Write-Host "  > Frontend: Check manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URLs:" -ForegroundColor White
Write-Host "  Frontend: https://$Domain" -ForegroundColor Gray
Write-Host "  API Docs: https://$Domain/docs" -ForegroundColor Gray
Write-Host "  Health:   https://$Domain/health" -ForegroundColor Gray
Write-Host ""
Write-Host "New Features Deployed:" -ForegroundColor Cyan
Write-Host "  - Flutter UI updates (Shimmer, Markdown, Image preview, Swipe delete)" -ForegroundColor Gray
Write-Host "  - New API: DELETE /meals/{id}" -ForegroundColor Gray
Write-Host "  - New API: GET /users/me/dashboard" -ForegroundColor Gray
Write-Host ""
