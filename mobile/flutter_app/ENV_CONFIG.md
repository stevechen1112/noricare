# 🚀 Flutter App 環境配置說明

## API 環境切換方式

### 1. 本地開發（預設）
```bash
# 使用 localhost（適用於模擬器/本機）
flutter run
```

### 2. 真機測試（需修改配置）
修改 `lib/config/api_config.dart`：
```dart
return 'http://YOUR_LOCAL_IP:8000/api/v1';  // 例如：http://192.168.1.100:8000/api/v1
```

或使用命令行參數：
```bash
flutter run --dart-define=ENV=development
```

### 3. 測試環境
```bash
flutter run --dart-define=ENV=staging
```

### 4. 正式環境
```bash
flutter run --dart-define=ENV=production
flutter build apk --dart-define=ENV=production
flutter build ipa --dart-define=ENV=production
```

## 如何查詢您的本機 IP

### Windows
```powershell
ipconfig | findstr IPv4
```

### macOS/Linux
```bash
ifconfig | grep "inet "
```

## 環境變數說明

| 環境 | ENV 值 | baseUrl |
|-----|--------|---------|
| 本地開發 | development (預設) | http://localhost:8000/api/v1 |
| 測試環境 | staging | https://staging-api.personalhealth.com/api/v1 |
| 正式環境 | production | https://api.personalhealth.com/api/v1 |

## 表單驗證規則

### Profile 表單
- **姓名**：必填，至少 2 個字元
- **年齡**：必填，1-120 歲
- **身高**：必填，50-250 cm
- **體重**：必填，20-300 kg

驗證失敗時會在欄位下方顯示錯誤訊息，確保數據質量。
