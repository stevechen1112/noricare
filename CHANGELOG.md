# 📝 專案更新日誌 (CHANGELOG)

> 記錄 Personal Health 專案的重要更新與版本變更

---

## [v1.2.1] - 2026-01-17

### 🚀 LLM 模型選擇與性能優化

#### ✨ 技術決策
- **正式採用 Gemini 3 Flash 模型**：`gemini-3-flash-preview`
  - 替換原先的 `gemini-3-pro-preview`
  - 速度提升 2.7 倍，品質相同
  - 適合實時應用場景

#### 📊 性能對比測試結果
完整對比測試（使用真實健檢圖片與報告生成任務）：

| 指標 | Flash (gemini-3-flash-preview) | Pro (gemini-3-pro-preview) | Flash 優勢 |
|------|--------------------------------|----------------------------|------------|
| OCR 平均速度 | **14.91 秒** | 41.41 秒 | **快 2.8 倍** ⚡ |
| 報告生成速度 | **11.13 秒** | 27.8 秒 | **快 2.5 倍** ⚡ |
| 報告品質評分 | 5/5 (1062 字) | 5/5 (1187 字) | **相同品質** |
| 完整流程總耗時 | **26 秒** | 69 秒 | **快 2.7 倍** ⚡ |

#### 🔧 更新內容
- `.env`：更新 `GEMINI_MODEL_NAME=gemini-3-flash-preview`
- `app/core/config.py`：更新預設模型為 Flash
- `app/services/ocr_service.py`：更新預設模型為 Flash
- `test_model_comparison.py`：新增 Pro vs Flash 自動化對比測試腳本

#### 💡 選擇理由
1. **速度優勢明顯**：OCR 與報告生成速度均快 2.5-2.8 倍
2. **品質完全相同**：兩者品質評分均為 5/5 滿分
3. **成本更低**：Flash 模型 API 使用成本更經濟
4. **用戶體驗更佳**：26 秒完成完整流程（vs Pro 的 69 秒）

#### 📚 文檔更新
- ✅ 新增模型對比測試結果文檔
- ✅ 更新測試腳本與結果 JSON

---

## [v1.2.0] - 2026-01-17

### 🎉 重大更新：Flutter App 核心功能完成

#### ✨ 新增功能
- **Flutter 跨平台 App**：iOS / Android / Windows 完整支援
  - 個人資料管理頁（Profile Page）
  - 健檢報告上傳頁（Upload Page）
  - 健康儀表板（Dashboard Page）
  - AI 對話頁（Chat Page）

- **表單驗證系統**：
  - 姓名驗證（≥2 字元）
  - 年齡驗證（1-120 歲）
  - 身高驗證（50-250 cm）
  - 體重驗證（20-300 kg）
  - 即時錯誤提示與紅字標記

- **API 環境配置系統**：
  - 支援 development / staging / production 三種環境
  - 使用 `--dart-define=ENV=xxx` 切換環境
  - 真機測試 IP 配置說明
  - Dio 日誌攔截器（Debug 模式自動開啟）

- **Chat UX 優化**：
  - 自動捲動到最新訊息
  - 顯示訊息時間戳記（HH:MM 格式）
  - 輸入中提示（Typing indicator）
  - 清除對話功能（含確認彈窗）

#### 🔧 技術改進
- 狀態管理：Riverpod 2.6.1 統一管理全局狀態
- HTTP Client：Dio 5.9.0 + 環境配置 + 日誌攔截
- 圖表可視化：fl_chart 0.68.0 趨勢圖表
- 圖片處理：image_picker 支援相機與相簿

#### 📚 文檔更新
- ✅ 新增專案根目錄 `README.md`（完整系統說明）
- ✅ 更新 `mobile/flutter_app/README.md`（Flutter App 詳細文檔）
- ✅ 新增 `mobile/flutter_app/ENV_CONFIG.md`（環境配置指南）
- ✅ 更新 `04_開發任務計畫_TaskPlan.md`（Phase 4 標記為已完成）
- ✅ 更新 `01_技術規格文件_MVP核心架構.md`（加入 Flutter App 狀態）

#### 🐛 修復問題
- Windows 首次運行需啟用開發人員模式（已加入文檔說明）
- Flutter SDK 環境變數配置問題
- Chat 頁面缺少 `fromJson` 方法

---

## [v1.1.0] - 2025-12

### ✨ 新增功能
- **對話式 AI 互動**：
  - 在報告頁面新增 "Ask Nutritionist" 視窗
  - 上下文管理（記住報告內容與知識庫）
  - 個人化對話回應

- **趨勢追蹤功能**：
  - 後端自動撈取使用者歷史記錄
  - AI 邏輯加入「上次數據對比」
  - Dashboard 新增趨勢圖表

- **RAG 知識庫整合**：
  - 導入台灣衛福部每日飲食指南
  - 藥物交互作用資料庫
  - 保健食品安全性指南
  - Keyword Filtering 優化檢索

#### 🎨 UI/UX 改進
- 返回/修改流程導覽
- 側邊欄導覽與進度顯示
- 主頁步驟條（可點擊切換）

---

## [v1.0.0] - 2025-11

### 🎉 首次發布：核心 MVP

#### ✨ 核心功能
- **多模態 OCR 引擎**：
  - 整合 Gemini Vision API
  - 自動提取結構化數據
  - 異常指標智能判讀

- **AI 營養推薦系統**：
  - 三段式建議（食療、補充品、菜單）
  - Gemini Pro 驅動
  - 個人化 Prompt 工程

- **系統架構**：
  - FastAPI 後端框架
  - SQLite + SQLAlchemy ORM
  - Streamlit Web 介面

#### 📊 數據處理
- 支援 15 個核心健康指標
- 單位自動轉換
- 信心評分機制
- 缺失數據降級處理

---

## 版本號規則

遵循 [Semantic Versioning](https://semver.org/)：

- **Major (X.0.0)**：重大架構變更或不向下相容
- **Minor (0.X.0)**：新增功能，向下相容
- **Patch (0.0.X)**：Bug 修復或微調

---

## 未來規劃

### v1.3.0（預計 2026-02）
- [ ] 報告歷史列表 + 詳細頁
- [ ] JWT 認證系統
- [ ] 推播通知功能
- [ ] iOS/Android 真機測試

### v1.4.0（預計 2026-03）
- [ ] App Store / Google Play 上架
- [ ] 多語言支援（英文/簡中）
- [ ] 離線模式
- [ ] Apple Health / Google Fit 整合

### v2.0.0（預計 2026-Q2）
- [ ] 社群功能（健康挑戰、排行榜）
- [ ] 營養師線上諮詢預約
- [ ] 進階數據分析（AI 預測模型）
- [ ] Docker 化部署與 CI/CD

---

**維護者**：Personal Health Team  
**授權**：MIT License
