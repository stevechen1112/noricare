# 🎨 App Icon 設置指南

## 需要的圖片檔案

### 1. app_icon.png（必須）
- **尺寸**：1024 x 1024 px
- **格式**：PNG（背景透明或實色皆可）
- **用途**：主要 App 圖標

### 2. app_icon_foreground.png（Android Adaptive Icon）
- **尺寸**：1024 x 1024 px（實際內容置中在 66% 區域）
- **格式**：PNG 透明背景
- **用途**：Android 12+ 自適應圖標前景

## 設計建議

### 🌿 Personal Health App 主題
- **主色**：橄欖綠 (#6B8E23)
- **輔色**：土橙色 (#D2691E)
- **背景**：米白色 (#FAF9F6)

### 圖標概念建議
1. 🌿 綠葉 + 心臟 = 健康生活
2. 📊 圖表 + 人物 = 數據追蹤
3. 🍎 蘋果/水果 + AI = 智能營養

## 生成圖標命令

準備好圖片後，執行：
```bash
flutter pub get
dart run flutter_launcher_icons
```

## 臨時方案（無設計師）

可以使用 AI 生成工具：
1. DALL-E 3 / Midjourney
2. Canva App Icon 模板
3. Figma + Icon 模板

提示詞範例：
```
A modern app icon for a health tracking app, featuring a green leaf merging with a heart shape, minimalist flat design, olive green (#6B8E23) color scheme, white background, suitable for iOS and Android
```
