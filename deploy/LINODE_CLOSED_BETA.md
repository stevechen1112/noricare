# Linode 封閉多人測試部署（Docker Compose + Caddy HTTPS）

目標：用一台 Linode VM 快速上線做封閉多人測試（email/password + JWT + Postgres），並用 Caddy 自動處理 HTTPS。

## 1) Linode 建機與 DNS
1. 建立 Linode（建議：Ubuntu 22.04/24.04，2GB RAM 起跳；多人測試建議 4GB）。
2. 設定網域 DNS A record 指向 Linode 公網 IP，例如：
   - `your-domain.example.com -> <LINODE_PUBLIC_IP>`

## 2) 安裝 Docker / Compose
Ubuntu：
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
# 重新登入後生效
```

## 3) 上傳專案到 Linode
方式 A：git clone
```bash
git clone <your-repo-url> personalhealth
cd personalhealth
```

方式 B：用 SCP/rsync 把整個專案目錄丟上去。

## 4) 準備 Flutter Web build（PWA 靜態檔）
在你的 CI 或本機先建置：
```bash
cd mobile/flutter_app
flutter build web
```
確認產物在 `mobile/flutter_app/build/web`。

若你不想在 Linode 上裝 Flutter，建議「在本機 build 完再上傳」整個 `build/web` 資料夾到 Linode 相同路徑。

## 5) 設定環境變數
在 Linode：
```bash
cd personalhealth/deploy
cp .env.linode.example .env.linode
nano .env.linode
```
必填：
- `APP_DOMAIN`（你的網域）
- `ACME_EMAIL`（用來申請 Let’s Encrypt）
- `GEMINI_API_KEY`
- `JWT_SECRET_KEY`（請用高強度隨機字串）
- `POSTGRES_PASSWORD`
- `BACKEND_CORS_ORIGINS`（至少放 `https://<APP_DOMAIN>`）

## 6) 啟動服務
```bash
cd personalhealth/deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build
```

看狀態：
```bash
docker compose --env-file .env.linode -f docker-compose.linode.yml ps
```

看 log：
```bash
docker compose --env-file .env.linode -f docker-compose.linode.yml logs -f --tail 200
```

## 7) 驗證
- 前端：打開 `https://<APP_DOMAIN>`
- API health：`https://<APP_DOMAIN>/health`
- API docs：`https://<APP_DOMAIN>/docs`

## 8) 封閉測試建議（最低安全門檻）
- `JWT_SECRET_KEY` 必須強且不可外流
- CORS 僅允許你的網域（`BACKEND_CORS_ORIGINS=https://<APP_DOMAIN>`）
- 建議 Linode Firewall 只開 80/443；SSH 限制你的 IP

## 9) 更新流程
```bash
cd personalhealth
git pull
cd deploy
docker compose --env-file .env.linode -f docker-compose.linode.yml up -d --build
```

---

如果你要「多環境」：可加 `APP_DOMAIN=beta.your-domain...`、對應不同 `.env` 與不同資料庫 volume 名稱。
