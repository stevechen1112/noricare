# Linode 部署前檢查清單

## ✅ 部署前準備 (Pre-Deployment)

### 本地環境檢查
- [ ] Flutter SDK 已安裝且版本 >= 3.3.0
- [ ] Git 工作區乾淨 (或已 commit 所有變更)
- [ ] `mobile/flutter_app/pubspec.yaml` 包含必要依賴:
  - [ ] `shimmer: ^3.0.0`
  - [ ] `flutter_markdown: ^0.7.4`
- [ ] Flutter web build 成功:
  ```powershell
  cd mobile/flutter_app
  flutter pub get
  flutter build web --release
  # 檢查 build/web/index.html 存在
  ```

### Backend 檢查
- [ ] Python 依賴完整 (檢查 `requirements.txt`)
- [ ] 新增 API endpoints 已實作:
  - [ ] `DELETE /api/v1/meals/{meal_id}` (app/api/v1/endpoints/meals.py)
  - [ ] `GET /api/v1/users/me/dashboard` (app/api/v1/endpoints/users.py)
- [ ] 本地測試通過:
  ```powershell
  python test_full_system_flow.py
  # 所有 5 個步驟應該通過
  ```

### Linode Server 準備
- [ ] SSH 存取正常: `ssh root@172.235.200.10`
- [ ] Docker 已安裝: `docker --version`
- [ ] Docker Compose 已安裝: `docker compose version`
- [ ] 磁碟空間充足: `df -h` (至少 5GB 可用)
- [ ] DNS A record 已設定且生效:
  ```bash
  nslookup noricare.app
  # 應該指向 Linode IP
  ```

---

## 🚀 部署步驟 (Deployment)

### 1. 執行自動部署腳本
```powershell
cd C:\Users\User\Desktop\personalhealth\tools

# 如果已完成 Flutter build，加上 -SkipFlutterBuild
.\deploy_linonde_closed_beta.ps1 `
  -ServerIp "172.235.200.10" `
  -ServerUser "root" `
  -Domain "noricare.app" `
  -SkipFlutterBuild
```

### 2. 檢查腳本輸出
部署腳本應該顯示以下 4 個步驟:
- [ ] ✓ Step 1/4: Flutter Web build (或跳過)
- [ ] ✓ Step 2/4: 專案上傳完成
- [ ] ✓ Step 3/4: Docker 服務已啟動
- [ ] ✓ Step 4/4: 驗證部署狀態

### 3. 檢查 Docker 服務狀態
```bash
ssh root@172.235.200.10
cd /root/personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml ps
```

預期輸出:
```
NAME                      STATUS         PORTS
personalhealth-api-1      Up X minutes   8000/tcp
personalhealth-db-1       Up X minutes   5432/tcp
personalhealth-caddy-1    Up X minutes   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

## 🔍 部署後驗證 (Post-Deployment Verification)

### Backend API 驗證
```bash
# 健康檢查 (應返回 200 OK)
curl -i https://noricare.app/health

# API 文件 (應顯示 Swagger UI)
curl -I https://noricare.app/docs

# 檢查新增 endpoints (需要 JWT token)
# 1. 先透過前端登入取得 token
# 2. 測試 DELETE meal:
curl -X DELETE https://noricare.app/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer {token}"

# 3. 測試 Dashboard:
curl https://noricare.app/api/v1/users/me/dashboard \
  -H "Authorization: Bearer {token}"
```

### Frontend 驗證
- [ ] 瀏覽器打開 `https://noricare.app` 成功載入
- [ ] Flutter app 啟動無錯誤 (檢查瀏覽器 Console)
- [ ] HTTPS 憑證有效 (瀏覽器顯示綠鎖)
- [ ] 前端功能測試:
  - [ ] 登入 / 註冊功能正常
  - [ ] Dashboard 顯示 Shimmer 載入動畫
  - [ ] Dashboard 載入完成顯示數據
  - [ ] Chat 頁面 AI 訊息顯示 Markdown 格式
  - [ ] Upload 頁面顯示圖片預覽網格
  - [ ] Meal Log 支援滑動刪除餐點

### 瀏覽器 DevTools 檢查
- [ ] Network tab: 所有 API 請求返回 200 (或預期的狀態碼)
- [ ] Console tab: **無 CORS 錯誤**
- [ ] Console tab: **無 JavaScript 錯誤** (正常運行可忽略 warning)
- [ ] Application tab: Service Worker 註冊成功 (PWA)

### 服務日誌檢查
```bash
# 檢查最近 100 行日誌
docker compose --env-file .env.linode -f docker-compose.linode.yml logs --tail 100

# 即時監控日誌 (Ctrl+C 退出)
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f

# 檢查錯誤訊息
docker compose --env-file .env.linode -f docker-compose.linode.yml logs | grep -i error
```

---

## ⚙️ 環境變數驗證

SSH 到 Linode server，檢查環境設定:

```bash
cd /root/personalhealth/deploy
cat .env.linode
```

### 必須設定的變數
- [ ] `APP_DOMAIN=noricare.app` (正確域名)
- [ ] `ACME_EMAIL=you@example.com` (用於 Let's Encrypt)
- [ ] `GEMINI_API_KEY=AIza...` (有效的 Google API key)
- [ ] `JWT_SECRET_KEY=...` (64+ 字元強隨機字串)
- [ ] `POSTGRES_PASSWORD=...` (強密碼)
- [ ] `BACKEND_CORS_ORIGINS=https://noricare.app` (**最重要!**)

### CORS 設定驗證
確保 `BACKEND_CORS_ORIGINS` 包含正確域名:
```bash
grep BACKEND_CORS_ORIGINS /root/personalhealth/deploy/.env.linode
# 必須包含: https://noricare.app
```

如果需要支援多個域名:
```bash
BACKEND_CORS_ORIGINS=https://noricare.app,https://beta.noricare.app
```

---

## 🐛 常見問題快速修復

### 問題 1: CORS 錯誤
**症狀**: 前端顯示網路錯誤，Console 顯示 CORS blocked

**修復**:
```bash
# 1. 編輯環境變數
nano /root/personalhealth/deploy/.env.linode
# 確保 BACKEND_CORS_ORIGINS=https://noricare.app

# 2. 僅重啟 API 服務
docker compose --env-file .env.linode -f docker-compose.linode.yml restart api

# 3. 驗證
curl -I https://noricare.app/health
# 應該看到: Access-Control-Allow-Origin header
```

### 問題 2: Frontend 空白頁
**症狀**: https://noricare.app 返回 200 但頁面空白

**修復**:
```bash
# 檢查 Flutter build 是否完整
ls -la /root/personalhealth/mobile/flutter_app/build/web/
# 應該看到: index.html, flutter.js, main.dart.js

# 如果檔案不完整，重新部署
# (在本機重新執行部署腳本)
```

### 問題 3: DELETE meal 返回 404
**症狀**: 刪除餐點失敗，返回 404

**可能原因**:
1. Meal 不屬於當前用戶
2. Meal ID 不存在

**檢查**:
```bash
# 查看 API logs
docker compose --env-file .env.linode -f docker-compose.linode.yml logs api | grep DELETE

# 確認 meal_id 格式正確 (應該是 UUID string)
```

### 問題 4: Docker build 失敗
**症狀**: `docker compose up` 時出現 build error

**修復**:
```bash
# 清除舊 image 和 cache
docker compose --env-file .env.linode -f docker-compose.linode.yml down
docker system prune -a -f

# 重新 build
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build
```

---

## 📊 效能監控

部署完成後，建議設定以下監控:

### 即時監控指令
```bash
# Docker 資源使用
docker stats

# 磁碟使用量
df -h

# 資料庫大小
docker compose --env-file .env.linode -f docker-compose.linode.yml exec db \
  psql -U personalhealth -c "SELECT pg_size_pretty(pg_database_size('personalhealth'));"

# 活躍連線數
docker compose --env-file .env.linode -f docker-compose.linode.yml exec api \
  ss -tlnp | grep 8000
```

### 自動監控建議
- [ ] 設定 Uptime monitoring (如 UptimeRobot, Pingdom)
  - 監控端點: `https://noricare.app/health`
  - 頻率: 每 5 分鐘
- [ ] 設定 Linode Longview (系統資源監控)
- [ ] 設定錯誤告警 (Email / Slack)

---

## 💾 備份計畫

### 資料庫備份
```bash
# 手動備份
docker compose --env-file .env.linode -f docker-compose.linode.yml exec -T db \
  pg_dump -U personalhealth personalhealth | gzip > /root/backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

# 設定自動備份 (cron job)
# 每日凌晨 2 點執行
crontab -e
# 加入:
0 2 * * * docker compose --env-file /root/personalhealth/deploy/.env.linode -f /root/personalhealth/deploy/docker-compose.linode.yml exec -T db pg_dump -U personalhealth personalhealth | gzip > /root/backups/db_$(date +\%Y\%m\%d).sql.gz

# 清理 30 天前的備份
0 3 * * * find /root/backups -name "db_*.sql.gz" -mtime +30 -delete
```

### 程式碼備份
```bash
# 部署前備份
cd /root
cp -r personalhealth personalhealth_backup_$(date +%Y%m%d)

# 保留最近 3 個版本
ls -dt personalhealth_backup_* | tail -n +4 | xargs rm -rf
```

---

## 🎯 最終檢查清單

完成以下所有項目後，部署視為成功:

- [ ] ✅ Backend API `/health` 返回 200
- [ ] ✅ Frontend `https://noricare.app` 正常載入
- [ ] ✅ HTTPS 憑證有效 (綠鎖)
- [ ] ✅ Dashboard 顯示 Shimmer 載入動畫
- [ ] ✅ Chat AI 訊息顯示 Markdown 格式
- [ ] ✅ Upload 頁面顯示圖片預覽
- [ ] ✅ Meal Log 支援滑動刪除
- [ ] ✅ DELETE meal API 測試成功
- [ ] ✅ GET dashboard API 測試成功
- [ ] ✅ 瀏覽器 Console 無 CORS 錯誤
- [ ] ✅ Docker logs 無嚴重錯誤
- [ ] ✅ 環境變數正確設定 (CORS, JWT, API keys)
- [ ] ✅ 資料庫備份已設定
- [ ] ✅ 監控告警已設定

---

## 📞 支援資源

- **詳細部署文件**: [LINODE_UPDATE_GUIDE.md](./LINODE_UPDATE_GUIDE.md)
- **部署腳本**: [tools/deploy_linonde_closed_beta.ps1](../tools/deploy_linonde_closed_beta.ps1)
- **Docker Compose 配置**: [docker-compose.linode.yml](./docker-compose.linode.yml)
- **環境變數範例**: [.env.linode.example](./.env.linode.example)

---

**最後更新**: 2026-01-19  
**版本**: v1.1 (包含 UI 更新 + 新 API endpoints)
