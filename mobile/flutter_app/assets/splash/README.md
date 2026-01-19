# 🚀 Splash Screen 設置指南

## 需要的圖片檔案

### splash_logo.png
- **尺寸**：512 x 512 px（建議）
- **格式**：PNG 透明背景
- **用途**：啟動畫面中心 Logo

## 設計建議

### 🌿 Personal Health App 主題
- **背景色**：米白色 (#FAF9F6)
- **Logo 主色**：橄欖綠 (#6B8E23)

### Logo 概念
- 可以使用與 App Icon 相同的設計
- 或使用文字 Logo：「My Health Coach」+ 圖示

## 生成啟動畫面命令

準備好圖片後，執行：
```bash
dart run flutter_native_splash:create
```

## 啟動畫面配置（已在 pubspec.yaml 設定）

```yaml
flutter_native_splash:
  color: "#FAF9F6"        # 背景色
  image: "assets/splash/splash_logo.png"
  android: true
  ios: true
```
