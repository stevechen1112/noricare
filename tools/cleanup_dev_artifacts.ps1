Param(
  [switch]$RemoveDb,
  [switch]$RemoveVenv
)

$ErrorActionPreference = 'Stop'

function Remove-IfExists([string]$Path) {
  if (Test-Path $Path) {
    try {
      Write-Host "[cleanup] Removing $Path"
      Remove-Item -Force -Recurse $Path -ErrorAction Stop
    } catch {
      Write-Warning "[cleanup] Skip (in use or protected): $Path"
    }
  }
}

function Remove-FileIfExists([string]$Path) {
  if (Test-Path $Path) {
    try {
      Write-Host "[cleanup] Removing $Path"
      Remove-Item -Force $Path -ErrorAction Stop
    } catch {
      Write-Warning "[cleanup] Skip (in use or protected): $Path"
    }
  }
}

Write-Host "[cleanup] Starting dev artifact cleanup..."

# Python caches
Get-ChildItem -Path . -Recurse -Directory -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -eq '__pycache__' } |
  ForEach-Object { Remove-IfExists $_.FullName }

Get-ChildItem -Path . -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like '*.pyc' } |
  ForEach-Object { Remove-Item -Force $_.FullName }

# Logs
Remove-IfExists "./logs"
Remove-FileIfExists "./streamlit_start.log"
Remove-FileIfExists "./logs/streamlit_stdout.log"
Remove-FileIfExists "./logs/streamlit_stderr.log"

# Uploads (generated)
Remove-IfExists "./uploads"

# UI smoke artifacts
Get-ChildItem -Path . -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like 'ui_smoke_*.png' } |
  ForEach-Object { Remove-Item -Force $_.FullName }

# Playwright browser cache
Remove-IfExists "./ms-playwright"

# Flutter build outputs + caches
Remove-IfExists "./mobile/flutter_app/build"
Remove-IfExists "./mobile/flutter_app/.dart_tool"
Remove-FileIfExists "./mobile/flutter_app/.flutter-plugins"
Remove-FileIfExists "./mobile/flutter_app/.flutter-plugins-dependencies"
Remove-FileIfExists "./mobile/flutter_app/.packages"

if ($RemoveDb) {
  Remove-FileIfExists "./sql_app.db"
}

if ($RemoveVenv) {
  Remove-IfExists "./.venv"
}

Write-Host "[cleanup] Done."
Write-Host "[cleanup] Tip: run with -RemoveDb to reset local accounts/data."
