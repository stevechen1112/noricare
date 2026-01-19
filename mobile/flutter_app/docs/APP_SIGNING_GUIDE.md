# App 簽署指南

## 📱 Android 簽署

### 步驟 1：生成 Keystore

打開終端機，執行以下命令生成金鑰：

```bash
keytool -genkey -v -keystore upload-keystore.jks -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

系統會要求輸入：
- **Keystore 密碼**：自訂密碼（請牢記！）
- **金鑰密碼**：可與 Keystore 密碼相同
- **姓名**：您的名字或公司名稱
- **組織單位**：部門名稱（可選）
- **組織**：公司名稱（可選）
- **城市**：所在城市
- **省/州**：所在省份
- **國家代碼**：TW（台灣）

### 步驟 2：移動 Keystore 文件

將生成的 `upload-keystore.jks` 移動到 Android 專案目錄：

```bash
# Windows
move upload-keystore.jks android\app\

# macOS/Linux
mv upload-keystore.jks android/app/
```

### 步驟 3：建立 key.properties

在 `android/` 目錄下建立 `key.properties` 文件：

```properties
storePassword=<你的 keystore 密碼>
keyPassword=<你的 key 密碼>
keyAlias=upload
storeFile=app/upload-keystore.jks
```

⚠️ **重要：請將 `key.properties` 加入 `.gitignore`！**

### 步驟 4：配置 build.gradle

編輯 `android/app/build.gradle`：

```groovy
// 在 android { 之前加入
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    // ... 現有配置 ...

    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### 步驟 5：建置 Release APK/AAB

```bash
# 建置 APK（用於測試）
flutter build apk --release

# 建置 App Bundle（用於 Google Play 上架）
flutter build appbundle --release
```

輸出位置：
- APK: `build/app/outputs/flutter-apk/app-release.apk`
- AAB: `build/app/outputs/bundle/release/app-release.aab`

---

## 🍎 iOS 簽署

### 前置需求

1. macOS 電腦（必須）
2. Apple Developer 帳號（年費 $99 USD）
3. Xcode 已安裝

### 步驟 1：註冊 Apple Developer

1. 前往 [developer.apple.com](https://developer.apple.com)
2. 註冊 Apple Developer Program
3. 支付年費 $99 USD

### 步驟 2：建立 App ID

1. 登入 [Apple Developer Console](https://developer.apple.com/account)
2. 前往 Certificates, Identifiers & Profiles
3. 選擇 Identifiers → 點擊 + 號
4. 選擇 App IDs → Continue
5. 填入：
   - Description: My Health Coach
   - Bundle ID: com.yourcompany.myhealthcoach
6. 勾選需要的 Capabilities（如 Push Notifications）
7. Register

### 步驟 3：建立憑證

1. 在 Certificates 頁面點擊 + 號
2. 選擇 iOS Distribution (App Store and Ad Hoc)
3. 依照指示在 Keychain Access 建立 CSR 檔案
4. 上傳 CSR 並下載憑證
5. 雙擊安裝憑證到 Keychain

### 步驟 4：建立 Provisioning Profile

1. 在 Profiles 頁面點擊 + 號
2. 選擇 App Store
3. 選擇您的 App ID
4. 選擇您的憑證
5. 命名並下載 Profile
6. 雙擊安裝

### 步驟 5：在 Xcode 配置

1. 打開 `ios/Runner.xcworkspace`
2. 選擇 Runner Target
3. 在 Signing & Capabilities 中：
   - Team: 選擇您的 Team
   - Bundle Identifier: com.yourcompany.myhealthcoach
   - 勾選 Automatically manage signing 或手動選擇 Profile

### 步驟 6：建置 Release

```bash
# 在專案根目錄執行
flutter build ios --release

# 或在 Xcode 中
# Product → Archive
```

### 步驟 7：上傳到 App Store Connect

1. 在 Xcode 選擇 Product → Archive
2. Archive 完成後，選擇 Distribute App
3. 選擇 App Store Connect → Upload
4. 依照提示完成上傳

---

## 🔐 安全提醒

### 不要 commit 到 Git 的文件

請確保 `.gitignore` 包含：

```gitignore
# Android 簽署
android/key.properties
android/app/*.jks
android/app/*.keystore
*.jks
*.keystore

# iOS 簽署
ios/*.mobileprovision
ios/*.p12
```

### 備份重要文件

請妥善備份以下文件（遺失將無法更新 App）：

1. **Android**
   - `upload-keystore.jks`
   - `key.properties`
   - Keystore 密碼

2. **iOS**
   - Distribution Certificate (.p12)
   - Certificate 密碼
   - Provisioning Profile

建議將這些文件加密後存放在安全的地方（如密碼管理器或保險箱）。

---

## 📋 檢查清單

### Android 上架前
- [ ] Keystore 已建立並備份
- [ ] key.properties 已配置且加入 .gitignore
- [ ] build.gradle 已配置簽署
- [ ] Release APK/AAB 已成功建置
- [ ] 已在真機上測試 Release 版本

### iOS 上架前
- [ ] Apple Developer 帳號已註冊
- [ ] App ID 已建立
- [ ] Distribution Certificate 已建立
- [ ] Provisioning Profile 已建立
- [ ] Xcode 簽署配置正確
- [ ] Archive 已成功建立
- [ ] 已在真機上測試 Release 版本

---

## 🆘 常見問題

### Android: Keystore 密碼忘記
**解決方案**：無法恢復，需要建立新的 Keystore。但這意味著您需要以新 App 身份重新上架。

### iOS: Provisioning Profile 過期
**解決方案**：在 Apple Developer Console 重新建立並下載新的 Profile。

### 建置失敗: Signing configuration missing
**解決方案**：確認 `key.properties` 路徑正確，且 `build.gradle` 配置無誤。

---

## 📚 參考資源

- [Flutter Android 部署官方文件](https://docs.flutter.dev/deployment/android)
- [Flutter iOS 部署官方文件](https://docs.flutter.dev/deployment/ios)
- [Google Play Console](https://play.google.com/console)
- [App Store Connect](https://appstoreconnect.apple.com)
