# 2026 拍照辨識食材＋份量估算＋營養/卡路里：實務可行性評估（針對 personalhealth 專案）

更新日期：2026-01-18

## 目標定義（避免落入「看起來很強但不可驗收」）

你要的能力其實是三段鏈：

1. **照片 → 食物/成分識別（What）**
2. **照片 → 份量/重量估算（How much, grams）**
3. **(食物ID, grams) → 營養素/熱量（Nutrition）**

在本專案中，第 3 段已具備可靠基礎：台灣食品營養資料庫的數值是「每 100g 可食部分」，系統只要拿到 grams 就能落地計算。
真正的高風險在第 2 段（幾何/尺度/密度）。

---

## A. 核心識別與營養分析（The Brain）— 2026 可用方案與落地方式

### A1. OpenAI 視覺模型（雲端）

**官方能力摘要（可落地點）**
- API 支援圖片輸入（URL/Base64/File），可一次輸入多張。
- 圖片計價以「影像 token」計，且可用 `detail=low/high/auto` 影響成本與解析度。
- 已知限制包含：空間推理/精準定位弱、計數是近似、會有錯誤描述風險。

參考：
- https://platform.openai.com/docs/guides/vision
- https://platform.openai.com/docs/guides/structured-outputs

**在本專案的建議用法**
- 用 Structured Outputs（JSON Schema）要求模型輸出結構化結果，避免 UI/後端解析困難。
- 輸出只做「候選食物名稱/成分 + 信心 + 份量文字描述（可選）」；營養數字一律由台灣 DB 計算（避免 hallucination）。

### A2. Google Gemini 視覺（雲端）

**官方能力摘要（可落地點）**
- `generateContent` 支援圖片（inline bytes 或 Files API），有 20MB inline 限制。
- 提供物件偵測（bounding boxes）與分割（segmentation masks）能力，輸出可指定 `application/json`。
- 提供 token/tiles 計價說明，並有 `media_resolution` 控制細節成本。

參考：
- https://ai.google.dev/gemini-api/docs/vision

**在本專案的建議用法**
- 若你要更進一步做「食物區塊分割」：Gemini 的 segmentation JSON 輸出對接後端會相對直覺。
- 但仍要注意：分割得到的是像素遮罩，不等於重量；重量仍需深度/尺度/密度。

### A3. Meta Llama 4（自架/私有化）

**官方能力摘要（可落地點）**
- Llama 4 Scout/Maverick 被標示為「natively multimodal」且支援影像＋文字理解。
- 適合醫療/隱私要求高、要私有化部署與成本可控的情境。

參考：
- https://www.llama.com/docs/

**在本專案的建議用法**
- 如果你的產品走向「醫療/保險/企業方案」且對 PHI 隱私要求高：Llama 4 是合理選項。
- 但自架意味著：GPU/推論服務/監控/更新成本都要自己扛，且 vision 模型推論常比純文字重。

---

## B. 份量與體積估算（The Geometry）— 哪些方案能做、準度落點在哪

### B1. iOS LiDAR + ARKit（高階、準度最佳）

**官方可取得資料**
- ARKit 的 `ARDepthData` 提供：
  - `depthMap`：每像素距離（單位：公尺）
  - `confidenceMap`：每像素深度信心
- 需透過 `ARWorldTrackingConfiguration` 開啟 scene depth 相關 frame semantics。

參考：
- https://developer.apple.com/documentation/arkit/ardepthdata

**可落地的工程路線（需要 iOS 原生）**
1. 食物分割：從影像模型取得 mask（Gemini segmentation / 自建 segmentation / 其他模型）。
2. 平面估計：偵測餐盤/桌面平面，建立 0 高度基準。
3. 深度投影：用 `depthMap` 將 mask 內像素轉成 3D 點雲。
4. 體積估算：對點雲做 voxelization 或 mesh 重建，得到體積 (cm³)。
5. 體積→重量：用「密度表」換算 grams（依食物類型、烹調含水量而變）。

**風險/成本**
- 優點：在 consumer 手段中最接近可用的「物理量測」。
- 缺點：你現有專案（Python/FastAPI/Flutter）沒有 iOS 原生 ARKit pipeline；要做需要新增 iOS 原生模組或 Flutter platform channel。

### B2. 單目深度（Monocular Depth Estimation，例如 Depth Anything）

**現況與能力**
- Depth Anything 提供相對深度（relative）且也有 metric depth 的 fine-tune 範例；授權 Apache-2.0。

參考：
- https://github.com/LiheYoung/Depth-Anything

**關鍵限制（為什麼常做不準）**
- 單張照片缺乏「絕對尺度」：即使深度形狀合理，沒有參考物就很難把 cm³ 轉成真實世界尺寸。

**能落地的折衷**
- 要求使用者放入參考物（硬幣/信用卡/標準湯匙/餐具），或使用「已知尺寸的餐盤」作為尺度。
- 先把目標改成「自動給出一個預估 grams + 讓使用者滑桿校正」，把最後責任留在使用者確認。

### B3. 多視角/短影片 photogrammetry（中高準度、UX 成本高）

- Nutrition5k 類型研究常用多角度掃描，甚至 overhead RGB-D（深度相機）。
- App 端可行方案是：引導使用者拍 3–5 張不同角度，雲端重建。

參考資料集（用於理解研究可達的上限與資料需求）：
- Nutrition5k（5k 盤餐，含 per-ingredient grams 與 RGB-D / 多視角）
  - https://github.com/google-research-datasets/Nutrition5k

**注意：資料集偏差**
- Nutrition5k 主要是美國 cafeteria，料理型態/食材與台灣便當、家常菜差異大，直接拿來做台灣場景的重量估算不一定準。

---

## C. 商業 API 捷徑（時間換錢）

### C1. LogMeal
- 官網公開宣稱支援 Food Quantity Detection、Nutritional Information 等。

參考：
- https://www.logmeal.com/api

**實務評估**
- 優點：最快把「看起來像全自動」做出來，且包含成分/菜餚層次輸出。
- 風險：
  - 成本、授權與速率限制
  - 黑盒：份量估算方法不可控
  - 標籤落地仍需對齊到台灣 DB（本專案的 alignment layer 正好可以處理這件事）

### C2. Passio
- 官網公開宣稱提供 Image Detection、Barcode、Nutrition Facts Detection、REST API 與 mobile SDK（含 Flutter）。

參考：
- https://www.passio.ai/nutrition-ai

**實務評估**
- 優點：行動端整合門檻低（Flutter 友善），也提供 Web API。
- 風險：
  - token 計費模式需要嚴格做「usage gate」
  - 同樣要做「Passio 食物標籤 → 台灣 DB 整合編號」的 mapping（你現有對齊機制可用）

---

## D. 針對 personalhealth 的推薦落地路線（可驗收、可持續迭代）

### D1. 先把「拍照 → 候選食物」做出來（MVP-1，最推薦）
**目標**：降低輸入成本，但不承諾全自動 grams。
1. 使用者拍照/上傳
2. Vision LLM 輸出候選食物清單（Top-N）與可選的成分拆解
3. 用現有 food alignment 對齊台灣 DB
4. UI 讓使用者：
   - 勾選真正吃的項目
   - 以「份量模板」或滑桿快速調整 grams（預設值可用類別平均）
5. 後端依台灣 DB 每 100g 計算營養

**為什麼這是最務實**：它把最不確定的「重量」留在使用者最後確認，結果可被驗收、也能累積真實資料做下一階段模型。

### D2. 半自動 grams（MVP-2）
**目標**：把 grams 初值變得更像「可用」。
- 方案 A：要求參考物（硬幣/卡片/餐具）
- 方案 B：引導多角度拍攝（3–5 張）
- 方案 C：iOS LiDAR（若你願意做 iOS 原生模組）

### D3. 真的要「全自動 grams」時，建議走二選一路線
- **隱私/控制優先**：Llama 4 + 自建 segmentation + LiDAR/參考物 + 密度表（成本高、長期護城河）
- **上市速度優先**：LogMeal/Passio（先跑起來，後續再逐步自建替換）

---

## E. 驗收方式（建議你一定要做，不然容易變成 demo）

1. 建一個小型驗收集：至少 100 張照片，涵蓋便當/火鍋/麵飯/飲料/水果。
2. 每張都要有「真實重量」參考（用秤量或包裝標示 + 可食比例）。
3. 指標建議：
   - 食物辨識 Top-3 命中率
   - grams 的 MAPE（平均百分比誤差）
   - 熱量 kcal 的 MAPE
4. UX 指標：完成一餐紀錄平均秒數、需要手動修正的比例。

---

## 結論（回答你原本那段建議：它是可落地的，但要分層做）

- Brain（識別）在 2026 已經很成熟：OpenAI/Gemini/Llama 4 都能做「看懂照片」並輸出結構化結果。
- Geometry（份量）仍是最難：要可用，幾乎一定需要 LiDAR、參考物、或多角度掃描；否則只能做「可被使用者校正」的估算。
- 對 personalhealth 來說，最佳 ROI 是先做 MVP-1：拍照減少打字、grams 由使用者校正，營養計算仍嚴格落地到台灣 DB。
