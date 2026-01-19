# Linode 部署更新指南 (2026-01-19)

## 📋 本次更新內容摘要

### 1. **Flutter 前端重大 UI 更新**
- ✅ 新增 **Shimmer 骨架屏載入效果** (dashboard_page.dart)
- ✅ 新增 **Markdown 渲染支援** (chat_page.dart)
- ✅ 新增 **圖片預覽網格** (upload_page.dart)
- ✅ 新增 **滑動刪除餐點功能** (meal_log_page.dart)
- ✅ 改善空狀態視覺設計

**新增 Flutter 依賴**:
- `shimmer: ^3.0.0`
- `flutter_markdown: ^0.7.4` (已存在)

### 2. **Backend API 新增功能**
- ✅ 新增 `DELETE /api/v1/meals/{meal_id}` - 刪除餐點
- ✅ 新增 `GET /api/v1/users/me/dashboard` - 儀表板數據
- ✅ 改善錯誤處理與 ownership 驗證

### 3. **資料庫 Schema**
- **無需 migration** - 所有新功能使用現有 schema
- DELETE endpoint 使用 cascade 刪除 MealItem

### 4. **環境變數**
- **無新增必要環境變數** - 所有功能基於現有配置
- 建議檢查: `BACKEND_CORS_ORIGINS` 是否包含正確域名

---

## 🚀 完整部署流程

### Step 1: 本地準備 Flutter Web Build

```powershell
# 在 Windows 開發機上執行
cd C:\Users\User\Desktop\personalhealth\mobile\flutter_app

# 確保依賴已安裝
flutter pub get

# 執行 Web 編譯 (產出到 build/web/)
flutter build web --release

# 驗證產出
ls build/web
# 應該看到: index.html, flutter.js, assets/, canvaskit/ 等
```

**⚠️ 重要**: 確保編譯成功且無錯誤，build/web 目錄完整。

---

### Step 2: 打包專案並上傳到 Linode

#### 方式 A: 使用現有自動化腳本 (推薦)

```powershell
cd C:\Users\User\Desktop\personalhealth\tools

# 執行部署腳本 (會自動 build + upload + 啟動)
.\deploy_linonde_closed_beta.ps1 `
  -ServerIp "172.235.200.10" `
  -ServerUser "root" `
  -Domain "noricare.app" `
  -IdentityFile "C:\Users\User\.ssh\your_key"

# 如果已經在 Step 1 完成 build，可加上 -SkipFlutterBuild:
.\deploy_linonde_closed_beta.ps1 `
  -ServerIp "172.235.200.10" `
  -ServerUser "root" `
  -Domain "noricare.app" `
  -SkipFlutterBuild
```

#### 方式 B: 手動上傳 (進階)

```powershell
# 1. 創建 tar 包 (排除不必要檔案)
cd C:\Users\User\Desktop\personalhealth
tar -czf personalhealth.tar.gz `
  --exclude=.venv `
  --exclude=__pycache__ `
  --exclude=logs `
  --exclude=uploads `
  --exclude=sql_app.db `
  --exclude=steve_personaldata `
  .

# 2. 上傳到 Linode
scp personalhealth.tar.gz root@172.235.200.10:/tmp/

# 3. SSH 登入解壓
ssh root@172.235.200.10
cd /root/personalhealth
tar -xzf /tmp/personalhealth.tar.gz
rm /tmp/personalhealth.tar.gz
```

---

### Step 3: 在 Linode 上重新部署服務

```bash
# SSH 到 Linode
ssh root@172.235.200.10

cd /root/personalhealth/deploy

# 檢查環境變數 (確認 CORS、JWT、API KEY 都已設定)
cat .env.linode

# 如果是第一次部署，需要複製範例檔案
# cp .env.linode.example .env.linode
# nano .env.linode  # 編輯必要變數

# 重新啟動所有服務 (會自動 rebuild Docker image)
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build

# 查看服務狀態
docker compose --env-file .env.linode -f docker-compose.linode.yml ps

# 查看啟動日誌 (確認無錯誤)
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f --tail 100
```

**預期輸出**:
```
NAME                      IMAGE                    STATUS         PORTS
personalhealth-api-1      personalhealth-api       Up 30 seconds  8000/tcp
personalhealth-db-1       postgres:16-alpine       Up 30 seconds  5432/tcp
personalhealth-caddy-1    caddy:2                  Up 30 seconds  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

### Step 4: 驗證部署

#### 4.1 健康檢查

```bash
# 在 Linode server 上測試
curl http://localhost:80/health
# 應該返回: {"status":"healthy"}

# 從本機測試 (替換成你的域名)
curl https://noricare.app/health
```

#### 4.2 測試前端載入

```bash
# 瀏覽器訪問
https://noricare.app

# 應該看到 Flutter app 載入
# 檢查瀏覽器 DevTools > Network > 確認 index.html, flutter.js 正常載入
```

#### 4.3 測試新增 API (DELETE meal)

```bash
# 需要先取得 JWT token (透過 frontend 登入)
# 或使用已有測試帳號

# 測試刪除 API (替換 {token} 和 {meal_id})
curl -X DELETE https://noricare.app/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer {token}"

# 應該返回: {"status":"deleted","meal_id":"..."}
```

#### 4.4 測試新增 API (Dashboard)

```bash
curl https://noricare.app/api/v1/users/me/dashboard \
  -H "Authorization: Bearer {token}"

# 應該返回 JSON 包含: userId, healthScore, keyMetrics[], abnormalItems[]
```

---

## 🔧 環境變數檢查清單

編輯 `/root/personalhealth/deploy/.env.linode`:

```bash
nano /root/personalhealth/deploy/.env.linode
```

**必須檢查的項目**:

| 變數名稱 | 當前值範例 | 說明 | 是否需更新 |
|---------|-----------|------|-----------|
| `APP_DOMAIN` | noricare.app | 你的域名 | ❌ (不變) |
| `ACME_EMAIL` | you@example.com | Let's Encrypt 郵箱 | ❌ (不變) |
| `GEMINI_API_KEY` | AIza... | Google Gemini API Key | ❌ (不變) |
| `JWT_SECRET_KEY` | (64+ chars) | JWT 簽名金鑰 | ❌ (不變) |
| `BACKEND_CORS_ORIGINS` | https://noricare.app | 允許的前端來源 | ⚠️ **檢查** |
| `POSTGRES_PASSWORD` | strong_password | 資料庫密碼 | ❌ (不變) |

**CORS 配置重點**:
- 必須包含 `https://noricare.app` (你的正式域名)
- 多個來源用逗號分隔: `https://noricare.app,https://beta.noricare.app`
- 本地測試可加: `http://localhost:8080`

---

## 🐛 常見問題排查

### 問題 1: 前端顯示 "網路錯誤" 或 CORS 錯誤

**症狀**: 
- 瀏覽器 Console 顯示: `Access-Control-Allow-Origin` 錯誤
- Flutter app 無法呼叫 API

**解決方式**:
```bash
# 檢查 CORS 設定
cd /root/personalhealth/deploy
grep BACKEND_CORS_ORIGINS .env.linode

# 應該包含正確域名，例如:
# BACKEND_CORS_ORIGINS=https://noricare.app

# 修改後重啟
docker compose --env-file .env.linode -f docker-compose.linode.yml restart api
```

---

### 問題 2: DELETE /meals API 返回 404

**症狀**: 
- 刪除餐點時返回 404 Not Found
- 即使 meal_id 正確

**可能原因**:
1. Meal 不屬於當前用戶 (ownership check 失敗)
2. Meal ID 格式錯誤 (UUID string)

**檢查方式**:
```bash
# 查看 API logs
docker compose --env-file .env.linode -f docker-compose.linode.yml logs api | grep DELETE

# 應該看到詳細錯誤訊息
```

---

### 問題 3: Flutter Web 顯示空白頁

**症狀**: 
- `https://noricare.app` 返回 200 但頁面空白
- 瀏覽器 Console 有 JavaScript 錯誤

**解決方式**:
```bash
# 1. 確認 Flutter build 是否完整
ls -la /root/personalhealth/mobile/flutter_app/build/web/
# 應該看到: index.html, flutter.js, main.dart.js, assets/

# 2. 檢查 Caddy 是否正確掛載
docker compose --env-file .env.linode -f docker-compose.linode.yml exec caddy ls -la /srv/web

# 3. 如果檔案缺失，重新上傳 build/web
# (在本機重新 flutter build web，然後 rsync 上傳)
```

---

### 問題 4: Shimmer 或 Markdown 無法顯示

**症狀**: 
- Dashboard 沒有骨架屏載入動畫
- Chat 頁面顯示純文字 (沒有 Markdown 格式)

**原因**: 
- Flutter 依賴未正確安裝或編譯

**解決方式**:
```powershell
# 在本機重新編譯
cd C:\Users\User\Desktop\personalhealth\mobile\flutter_app

# 清除快取
flutter clean
flutter pub get

# 重新編譯
flutter build web --release

# 重新部署到 Linode (參考 Step 2)
```

---

## 📊 部署後檢查清單

- [ ] ✅ Backend API health check 通過 (`/health`)
- [ ] ✅ Frontend 首頁載入正常 (Flutter app)
- [ ] ✅ 登入功能正常 (JWT token 取得)
- [ ] ✅ Dashboard 顯示 Shimmer 載入動畫
- [ ] ✅ Chat 頁面顯示 Markdown 格式
- [ ] ✅ Upload 頁面顯示圖片預覽網格
- [ ] ✅ Meal Log 支援滑動刪除
- [ ] ✅ DELETE /meals/{meal_id} API 正常運作
- [ ] ✅ GET /users/me/dashboard API 返回數據
- [ ] ✅ HTTPS 憑證有效 (Let's Encrypt)
- [ ] ✅ 瀏覽器 Console 無 CORS 錯誤
- [ ] ✅ Docker logs 無異常錯誤

---

## 🔄 回滾計畫 (緊急狀況)

如果部署後發現重大問題，可使用以下步驟回滾:

```bash
# 1. 停止當前服務
cd /root/personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml down

# 2. 恢復舊版本 (需要事先備份)
cd /root
mv personalhealth personalhealth_broken
mv personalhealth_backup personalhealth

# 3. 重新啟動舊版本
cd /root/personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build
```

**建議**: 部署前先備份:
```bash
cd /root
cp -r personalhealth personalhealth_backup_$(date +%Y%m%d)
```

---

## 📈 效能監控建議

部署後持續監控以下指標:

```bash
# CPU / Memory usage
docker stats

# Disk usage
df -h
du -sh /root/personalhealth/uploads
du -sh /var/lib/docker

# Active connections
docker compose --env-file .env.linode -f docker-compose.linode.yml exec api ss -tlnp | grep 8000

# Database size
docker compose --env-file .env.linode -f docker-compose.linode.yml exec db psql -U personalhealth -c "SELECT pg_size_pretty(pg_database_size('personalhealth'));"
```

---

## 🎯 下一步建議

1. **設定自動備份**:
   ```bash
   # 加入 cron job 每日備份資料庫
   0 2 * * * docker compose --env-file /root/personalhealth/deploy/.env.linode -f /root/personalhealth/deploy/docker-compose.linode.yml exec -T db pg_dump -U personalhealth personalhealth | gzip > /root/backups/db_$(date +\%Y\%m\%d).sql.gz
   ```

2. **設定監控告警**:
   - 使用 Uptime Kuma / Prometheus 監控 `/health` endpoint
   - 設定 Linode Monitoring alerts (CPU/Memory/Disk)

3. **效能優化**:
   - 啟用 Caddy 的 Brotli 壓縮
   - 配置 PostgreSQL connection pooling
   - 考慮加入 Redis cache (未來更新)

---

## 📞 技術支援

遇到問題請檢查:
1. Docker logs: `docker compose logs -f --tail 200`
2. Caddy logs: `docker compose exec caddy cat /data/caddy/logs/access.log`
3. 瀏覽器 DevTools > Console / Network

**本次更新完成時間**: 2026-01-19  
**Backend Port**: 8001 (dev) / 8000 (production container)  
**Database**: PostgreSQL 16 (production) / SQLite (dev)
