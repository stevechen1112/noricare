# 法律文件部署指南

本目錄包含 App 上架所需的法律文件。

## 📋 文件清單

| 文件 | 用途 | 狀態 |
|------|------|------|
| [privacy_policy.html](privacy_policy.html) | 隱私權政策 | ✅ 已建立 |
| [terms_of_service.html](terms_of_service.html) | 服務條款 | ✅ 已建立 |

## 🚀 部署方式

### 方式一：GitHub Pages（免費）

1. 建立新的 GitHub Repository（例如 `myhealthcoach-legal`）
2. 上傳 `docs/` 目錄下的 HTML 文件
3. 啟用 GitHub Pages（Settings → Pages → Source: main branch）
4. 取得 URL：`https://yourusername.github.io/myhealthcoach-legal/`

### 方式二：Netlify（免費）

1. 前往 [netlify.com](https://netlify.com)
2. 拖曳 `docs/` 資料夾到 Netlify
3. 取得免費 URL：`https://random-name.netlify.app/`

### 方式三：自有網站

將 HTML 文件上傳到您的網站伺服器，例如：
- `https://myhealthcoach.com/privacy`
- `https://myhealthcoach.com/terms`

## 📱 App Store 上架需求

### Google Play Console

在「Store Listing」→「Privacy Policy」填入：
```
https://yoursite.com/privacy_policy.html
```

### Apple App Store Connect

在 App Information 填入：
```
Privacy Policy URL: https://yoursite.com/privacy_policy.html
```

## ✏️ 需要修改的內容

請在上架前修改以下標記的內容：

### privacy_policy.html

1. `[公司名稱]` → 您的公司或個人名稱
2. `[請填入公司地址]` → 實際地址
3. `[請填入電話]` → 客服電話
4. `[雲端供應商]` → 例如 AWS、GCP、Azure
5. `privacy@myhealthcoach.com` → 實際聯絡信箱

### terms_of_service.html

1. `[公司名稱]` → 您的公司或個人名稱
2. `[請填入電話]` → 客服電話
3. `[請填入地址]` → 實際地址
4. `support@myhealthcoach.com` → 實際聯絡信箱

## 🔗 App 內整合

在 Flutter App 中加入隱私權政策連結：

```dart
import 'package:url_launcher/url_launcher.dart';

// 在登入頁面或設定頁面加入連結
TextButton(
  onPressed: () => launchUrl(
    Uri.parse('https://yoursite.com/privacy_policy.html'),
    mode: LaunchMode.externalApplication,
  ),
  child: Text('隱私權政策'),
),
```

## ⚠️ 法律提醒

1. 這些是範本文件，建議請法律專業人士審閱
2. 不同國家/地區可能有額外的法規要求
3. 若您的 App 收集健康敏感資料，可能需要符合 HIPAA（美國）或 GDPR（歐盟）等規範
4. 定期更新隱私權政策以反映實際的資料處理方式

## 📅 更新紀錄

- 2026-01-17：初版建立
