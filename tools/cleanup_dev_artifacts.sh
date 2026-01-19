#!/usr/bin/env bash
set -euo pipefail

REMOVE_DB=0
REMOVE_VENV=0

for arg in "$@"; do
  case "$arg" in
    --remove-db) REMOVE_DB=1 ;;
    --remove-venv) REMOVE_VENV=1 ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

echo "[cleanup] Starting dev artifact cleanup..."

# Python caches
find . -type d -name '__pycache__' -prune -exec rm -rf {} + || true
find . -type f -name '*.pyc' -delete || true

# Logs
rm -rf ./logs || true
rm -f ./streamlit_start.log || true

# Uploads (generated)
rm -rf ./uploads || true

# UI smoke artifacts
rm -f ./ui_smoke_*.png || true

# Playwright browser cache
rm -rf ./ms-playwright || true

# Flutter build outputs + caches
rm -rf ./mobile/flutter_app/build || true
rm -rf ./mobile/flutter_app/.dart_tool || true
rm -f ./mobile/flutter_app/.flutter-plugins || true
rm -f ./mobile/flutter_app/.flutter-plugins-dependencies || true
rm -f ./mobile/flutter_app/.packages || true

if [[ $REMOVE_DB -eq 1 ]]; then
  rm -f ./sql_app.db || true
fi

if [[ $REMOVE_VENV -eq 1 ]]; then
  rm -rf ./.venv || true
fi

echo "[cleanup] Done."
echo "[cleanup] Tip: use --remove-db to reset local accounts/data."
