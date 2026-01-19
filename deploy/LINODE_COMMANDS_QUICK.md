# Linode 快速部署命令參考

## 📦 一鍵部署 (本機執行)

```powershell
# 完整部署 (包含 Flutter build)
cd C:\Users\User\Desktop\personalhealth\tools
.\deploy_linonde_closed_beta.ps1 -ServerIp "172.235.200.10" -ServerUser "root" -Domain "noricare.app"

# 跳過 Flutter build (如果已經 build 過)
.\deploy_linonde_closed_beta.ps1 -ServerIp "172.235.200.10" -SkipFlutterBuild

# 使用 SSH key 認證
.\deploy_linonde_closed_beta.ps1 -IdentityFile "C:\Users\User\.ssh\id_rsa"
```

---

## 🖥️ Server 端常用指令 (SSH 執行)

### 連線到 Server
```bash
ssh root@172.235.200.10
cd /root/personalhealth/deploy
```

### Docker Compose 操作
```bash
# 啟動所有服務 (daemon mode)
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build

# 停止所有服務
docker compose --env-file .env.linode -f docker-compose.linode.yml down

# 重啟特定服務
docker compose --env-file .env.linode -f docker-compose.linode.yml restart api
docker compose --env-file .env.linode -f docker-compose.linode.yml restart caddy
docker compose --env-file .env.linode -f docker-compose.linode.yml restart db

# 查看服務狀態
docker compose --env-file .env.linode -f docker-compose.linode.yml ps

# 查看日誌 (最近 100 行)
docker compose --env-file .env.linode -f docker-compose.linode.yml logs --tail 100

# 即時監控日誌 (Ctrl+C 退出)
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f

# 只看特定服務日誌
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f api
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f caddy
```

### 環境變數管理
```bash
# 查看當前設定
cat .env.linode

# 編輯環境變數
nano .env.linode

# 編輯後重啟 API 服務使其生效
docker compose --env-file .env.linode -f docker-compose.linode.yml restart api
```

---

## 🔍 故障排查指令

### 檢查 Backend API
```bash
# 本機測試 (在 server 上)
curl http://localhost:80/health
curl http://localhost:80/docs

# 外部測試
curl https://noricare.app/health
curl https://noricare.app/docs

# 檢查 API 容器內部
docker compose --env-file .env.linode -f docker-compose.linode.yml exec api bash
# 進入後可執行:
python -c "from app.core.config import settings; print(settings.BACKEND_CORS_ORIGINS)"
```

### 檢查 Frontend
```bash
# 檢查 Flutter build 檔案
ls -la /root/personalhealth/mobile/flutter_app/build/web/

# 檢查 Caddy 是否掛載正確
docker compose --env-file .env.linode -f docker-compose.linode.yml exec caddy ls -la /srv/web

# 查看 Caddy 配置
docker compose --env-file .env.linode -f docker-compose.linode.yml exec caddy cat /etc/caddy/Caddyfile
```

### 檢查資料庫
```bash
# 進入 PostgreSQL
docker compose --env-file .env.linode -f docker-compose.linode.yml exec db psql -U personalhealth

# 查看資料庫大小
docker compose --env-file .env.linode -f docker-compose.linode.yml exec db \
  psql -U personalhealth -c "SELECT pg_size_pretty(pg_database_size('personalhealth'));"

# 查看表格數量
docker compose --env-file .env.linode -f docker-compose.linode.yml exec db \
  psql -U personalhealth -d personalhealth -c "\dt"

# 檢查連線數
docker compose --env-file .env.linode -f docker-compose.linode.yml exec db \
  psql -U personalhealth -c "SELECT count(*) FROM pg_stat_activity;"
```

### CORS 問題檢查
```bash
# 檢查 CORS 設定
grep BACKEND_CORS_ORIGINS /root/personalhealth/deploy/.env.linode

# 測試 CORS headers
curl -I -H "Origin: https://noricare.app" https://noricare.app/health

# 應該看到:
# Access-Control-Allow-Origin: https://noricare.app
```

### 資源使用監控
```bash
# Docker 容器資源
docker stats

# 系統資源
top
htop  # 如果已安裝

# 磁碟空間
df -h
du -sh /root/personalhealth/*
du -sh /var/lib/docker

# 網路連線
ss -tlnp | grep -E '80|443|8000|5432'
```

---

## 🛠️ 維護操作

### 清理 Docker 資源
```bash
# 停止所有服務
docker compose --env-file .env.linode -f docker-compose.linode.yml down

# 清理未使用的 images/containers/volumes
docker system prune -a

# ⚠️ 危險: 清理所有資料 (包含資料庫)
docker compose --env-file .env.linode -f docker-compose.linode.yml down -v

# 重新啟動
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build
```

### 資料庫備份 & 還原
```bash
# 備份資料庫
mkdir -p /root/backups
docker compose --env-file .env.linode -f docker-compose.linode.yml exec -T db \
  pg_dump -U personalhealth personalhealth | gzip > /root/backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

# 還原資料庫 (⚠️ 會覆蓋現有資料)
gunzip -c /root/backups/db_20260119_120000.sql.gz | \
  docker compose --env-file .env.linode -f docker-compose.linode.yml exec -T db \
  psql -U personalhealth personalhealth

# 列出所有備份
ls -lh /root/backups/

# 清理 30 天前的備份
find /root/backups -name "db_*.sql.gz" -mtime +30 -delete
```

### SSL 憑證更新
```bash
# Caddy 會自動更新，但如果需要手動觸發:
docker compose --env-file .env.linode -f docker-compose.linode.yml restart caddy

# 檢查憑證有效期
echo | openssl s_client -connect noricare.app:443 2>/dev/null | openssl x509 -noout -dates
```

---

## 🔄 更新流程

### 更新 Backend 程式碼
```bash
# 如果使用 git
cd /root/personalhealth
git pull

# 重新啟動 API (會重新 build)
cd deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build api
```

### 更新 Frontend (Flutter)
```powershell
# 在本機重新 build
cd C:\Users\User\Desktop\personalhealth\mobile\flutter_app
flutter build web --release

# 上傳到 server
cd C:\Users\User\Desktop\personalhealth\tools
.\deploy_linonde_closed_beta.ps1 -SkipFlutterBuild:$false
```

### 更新環境變數
```bash
# 編輯
nano /root/personalhealth/deploy/.env.linode

# 重啟服務使其生效
docker compose --env-file .env.linode -f docker-compose.linode.yml restart api
```

---

## 📊 監控指令

### 查看即時日誌
```bash
# 所有服務
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f --tail 50

# 只看 API
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f api

# 過濾錯誤
docker compose --env-file .env.linode -f docker-compose.linode.yml logs | grep -i error

# 過濾特定 endpoint
docker compose --env-file .env.linode -f docker-compose.linode.yml logs api | grep "DELETE /meals"
```

### 健康檢查循環
```bash
# 每 5 秒檢查一次 health endpoint
watch -n 5 "curl -s https://noricare.app/health | jq"

# 或使用簡單版本
while true; do curl https://noricare.app/health; sleep 5; done
```

---

## 🚨 緊急操作

### 快速重啟所有服務
```bash
cd /root/personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml restart
```

### 完全重新部署 (保留資料庫)
```bash
cd /root/personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml down
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build
```

### 緊急回滾
```bash
# 停止當前版本
cd /root/personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml down

# 恢復備份
cd /root
mv personalhealth personalhealth_broken
mv personalhealth_backup_20260119 personalhealth

# 啟動舊版本
cd /root/personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d
```

### 查看錯誤並重啟
```bash
# 查看最近錯誤
docker compose --env-file .env.linode -f docker-compose.linode.yml logs --tail 100 | grep -i error

# 如果 API 掛掉
docker compose --env-file .env.linode -f docker-compose.linode.yml restart api

# 如果資料庫掛掉
docker compose --env-file .env.linode -f docker-compose.linode.yml restart db

# 如果 Caddy 掛掉 (HTTPS/HTTP)
docker compose --env-file .env.linode -f docker-compose.linode.yml restart caddy
```

---

## 📝 常用環境變數範本

```bash
# /root/personalhealth/deploy/.env.linode

# Domain & TLS
APP_DOMAIN=noricare.app
ACME_EMAIL=admin@noricare.app

# Backend
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
GEMINI_MODEL_NAME=gemini-3-flash-preview
JWT_SECRET_KEY=REPLACE_WITH_64_CHAR_RANDOM_STRING_USE_openssl_rand_base64_48
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS (關鍵設定!)
BACKEND_CORS_ORIGINS=https://noricare.app

# Database
POSTGRES_DB=personalhealth
POSTGRES_USER=personalhealth
POSTGRES_PASSWORD=REPLACE_WITH_STRONG_PASSWORD

# Optional
PROJECT_NAME=NoriCare
```

生成強隨機密碼:
```bash
# JWT Secret (64+ chars)
openssl rand -base64 48

# PostgreSQL Password
openssl rand -base64 32
```

---

## 🔗 快速連結

- **Frontend**: https://noricare.app
- **API Docs**: https://noricare.app/docs
- **Health Check**: https://noricare.app/health
- **Server SSH**: `ssh root@172.235.200.10`

---

**更新日期**: 2026-01-19  
**包含更新**: Flutter UI 改進 + DELETE meals API + Dashboard API
