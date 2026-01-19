# 開發任務計畫（Task Plan）v2.0 - AI Agent 加速版

> **策略調整**：從傳統的功能堆疊開發，轉向 **AI Native** 開發模式。核心邏輯由 Gemini 3 Pro 驅動，專注於「上下文情境 (Context)」、「個人化 (Personalization)」與「互動體驗 (Experience)」。

---

## ✅ Phase 1: 核心 MVP (Completed)
**狀態：已完成**
- [x] **多模態 OCR 引擎**：整合 Gemini Vision API，直接從圖片提取結構化數據 + 異常判讀。
- [x] **AI 營養大腦**：封裝 `ai_service`，根據數據生成三段式建議（食療、補充品、菜單）。
- [x] **系統架構**：FastAPI 後端 + SQLite 資料庫 + SqlAlchemy ORM。
- [x] **生活化介面**：Streamlit 前端，具備「專屬營養師」Persona，包含生活型態問卷。

---

## 🚀 Phase 2: 深度個人化與記憶 (Current Focus)
**目標**：讓 Agent 具備「記憶」與「連續性照護」能力，不像是在看新病患，而是像老朋友一樣。

### 2.1 趨勢追蹤與比較 (Trend Analysis) 
- [x] **後端**：在生成建議時，自動撈取該 User 過去的 `HealthRecord`。
- [x] **AI 邏輯**：Prompt 工程優化，加入「上次數據對比」。
    - *情境*：「Steve，你的 HbA1c 從上次的 6.2% 降到 5.8%，雖然還在紅字，但飲食控制有效，請繼續保持！」
- [x] **前端**：在 Dashboard 新增「趨勢圖表」或「進步幅度」卡片。

### 2.2 知識庫掛載 (RAG & Grounding) (Optimized)
- [x] **建立知識庫**：導入「台灣衛福部每日飲食指南」、「drug_interactions」、「supplement_safety」。
- [x] **RAG 檢索**：建立 `KnowledgeService`，加入 Keyword Filtering 優化機制。
- [x] **食安守門**：針對「補充品建議」增加 "Safety Guardrails" Prompt 規則。

### 2.3 對話式互動 (Interactive Chat) (Completed)
- [x] **Chat Interface**：在報告頁面下方新增 "Ask Nutritionist" 視窗。
- [x] **Context管理**：對話時能「記住」上面的報告內容 與 專業知識庫。
    - *User*：「這週菜單的苦瓜可以換掉嗎？」
    - *AI*：「沒問題，考慮到您需要降血糖，我們可以換成秋葵或深綠色蔬菜...」

### 2.4 UI/UX 流程優化 (Completed)
- [x] **返回/修改流程**：Step 2/3 增加「返回上一步 / 修改資料」導覽。
- [x] **側邊欄導覽**：新增 Sidebar 導覽與進度顯示。
- [x] **主頁步驟條**：新增頂部水平進度條 + 可點擊步驟切換。

---

## 🛠 Phase 3: 產品化與擴展 (Future)
**目標**：從 Demo 走向 Production。

### 3.1 使用者帳戶與安全
- [ ] 實作 JWT Authentication (Login/Register)。
- [ ] 資料加密存儲 (尤其是醫療個資)。

### 3.2 多元輸入整合
- [ ] 支援 Apple Health / Google Fit 數據同步（步數、睡眠）。
- [ ] 支援手動輸入缺失的檢驗數值。

### 3.3 部署與維運
- [ ] Docker 化封裝。
- [ ] Cloud Run 部署架構設計。

---

## 📱 Phase 4: 行動版 App (Flutter) ✅ (Completed)
**目標**：iOS / Android / Windows 同步支援，延續 Web 體驗。

### 4.1 專案骨架與架構 ✅
- [x] 建立 Flutter 專案骨架 (資料夾結構、路由、主題)。
- [x] 建立 API Client (與 FastAPI 串接)。
- [x] 建立 Models (User/Report/History/Chat)。
- [x] 環境配置系統 (development/staging/production)。

### 4.2 UI/UX 介面 ✅
- [x] 個人資料建立頁 (Profile) + API 串接 + **表單驗證**
- [x] 上傳健檢報告 (Upload) + OCR/分析流程 + 拍照支援
- [x] 健康儀表板 (Dashboard) + 趨勢圖表 + 異常指標/建議卡片
- [x] AI Chat 互動頁 (已串接) + **UX 優化**（自動捲動、時間戳、清除對話）

### 4.3 整合與測試 ✅
- [x] API 串接與後端驗證 (Backend Verified)
- [x] 環境建置 (Flutter SDK 3.27.1 Installation)
- [x] Windows 桌面版運行成功
- [x] 基礎錯誤處理與狀態管理

### 4.4 品質優化 ✅ (2026-01-17)
- [x] **表單驗證系統**：姓名/年齡/身高/體重即時驗證，保障數據質量
- [x] **API 環境配置**：支援 dev/staging/prod 環境切換，真機測試友善
- [x] **Chat UX 改進**：
  - 自動捲動到最新訊息
  - 顯示時間戳記
  - 輸入中提示（Typing indicator）
  - 清除對話功能（含確認彈窗）
- [x] **API Client 優化**：Dio 日誌攔截器，Debug 模式自動開啟

### 4.5 待辦事項 (Future)
- [ ] 報告歷史列表 + 詳細頁
- [ ] iOS/Android 真機測試與上架準備
- [ ] 離線模式支援
- [ ] 推播通知功能

---
