# 🤖 LLM 模型選擇與性能分析

> Personal Health 專案的 AI 模型技術決策文檔

---

## 📋 目錄
- [技術決策](#技術決策)
- [性能對比測試](#性能對比測試)
- [測試方法](#測試方法)
- [結論與建議](#結論與建議)
- [未來展望](#未來展望)

---

## 🎯 技術決策

### 最終選擇：Gemini 3 Flash (`gemini-3-flash-preview`)

**決策日期**：2026-01-17

**選擇理由**：
1. ⚡ **速度優勢明顯**：比 Pro 版本快 2.7 倍
2. 💎 **品質完全相同**：與 Pro 版本品質評分均為 5/5
3. 💰 **成本更經濟**：API 使用成本更低
4. 👥 **用戶體驗更佳**：完整流程 26 秒 vs Pro 的 69 秒

---

## 📊 性能對比測試

### 測試環境
- **測試日期**：2026-01-17
- **測試機器**：Windows 11, Python 3.13
- **API 配置**：Google Generative AI Python SDK
- **測試數據**：真實台灣健檢報告圖片 (40108.jpg, 40109.jpg)

### 對比模型
1. **Gemini 3 Flash**：`gemini-3-flash-preview`
2. **Gemini 3 Pro**：`gemini-3-pro-preview`

---

## 🔬 測試結果

### 1️⃣ OCR 速度測試

測試任務：從健檢報告圖片中提取結構化數據（血糖、血壓、肝功能等 40+ 項目）

| 測試圖片 | Flash 耗時 | Pro 耗時 | 速度提升 |
|---------|-----------|----------|---------|
| 40108.jpg | 9.49 秒 | 38.21 秒 | **4.0 倍** ⚡ |
| 40109.jpg | 20.32 秒 | 44.61 秒 | **2.2 倍** ⚡ |
| **平均** | **14.91 秒** | **41.41 秒** | **2.8 倍** ⚡ |

**OCR 辨識準確度**：兩者均能成功提取 10+ 個健檢項目，準確度相同

---

### 2️⃣ 報告生成速度測試

測試任務：根據健檢數據生成 500 字以上的個人化營養建議報告

| 指標 | Flash | Pro | Flash 優勢 |
|------|-------|-----|-----------|
| **生成耗時** | **11.13 秒** | 27.8 秒 | **快 2.5 倍** ⚡ |
| **字數** | 1,062 字 | 1,187 字 | 相當 |
| **品質評分** | **5/5** | **5/5** | **完全相同** ✅ |

---

### 3️⃣ 完整流程總耗時

完整用戶流程：上傳圖片 → OCR 辨識 → AI 分析 → 生成報告

| 階段 | Flash | Pro | Flash 優勢 |
|------|-------|-----|-----------|
| OCR（2 張圖片） | 14.91 秒 | 41.41 秒 | 快 2.8 倍 |
| 報告生成 | 11.13 秒 | 27.8 秒 | 快 2.5 倍 |
| **總計** | **26.04 秒** | **69.21 秒** | **快 2.7 倍** ⚡ |

---

## 📈 品質分析

### Flash 報告範例（節錄）
```
好的，這位先生您好，我是您的營養師。根據您的健檢數據，血糖稍高，
糖化血色素也接近臨界值，顯示您有血糖控制的壓力。加上BMI值顯示您
有過重的情況，因此控制血糖和減重是您目前需要努力的方向。我將根據
您的情況，提供以下營養建議：

**1. 飲食建議：**

*   **控制碳水化合物攝取量與選擇：**
    *   **減少精緻澱粉：** 像是白飯、麵包、麵條、含糖飲料、餅乾等...
```

### 品質評分標準（5 分制）
- ✅ **結構完整性**（1 分）：章節清晰、邏輯流暢
- ✅ **內容準確性**（1 分）：基於健檢數據的精準分析
- ✅ **實用性**（1 分）：可執行的具體建議
- ✅ **專業性**（1 分）：營養學專業知識正確
- ✅ **個人化程度**（1 分）：針對個人數據客製化

**兩者均達成 5/5 滿分**

---

## 🧪 測試方法

### 測試腳本
```python
# test_model_comparison.py
def test_ocr_speed(model_name, image_path):
    """測試 OCR 速度與準確度"""
    start_time = time.time()
    result = genai.GenerativeModel(model_name).generate_content([
        "請分析這張台灣健檢報告圖片...",
        PIL.Image.open(image_path)
    ])
    elapsed = time.time() - start_time
    return {"time": elapsed, "field_count": count_fields(result)}

def test_report_generation(model_name):
    """測試報告生成速度與品質"""
    start_time = time.time()
    result = genai.GenerativeModel(model_name).generate_content(
        "根據以下健檢數據生成 500 字營養建議..."
    )
    elapsed = time.time() - start_time
    quality_score = evaluate_quality(result.text)
    return {"time": elapsed, "quality_score": quality_score}
```

### 執行方式
```bash
cd C:\Users\User\Desktop\personalhealth
.venv\Scripts\activate
python test_model_comparison.py
```

### 測試結果檔案
- `model_comparison_results.json`：完整測試數據（JSON 格式）
- `test_model_comparison.py`：自動化測試腳本

---

## 💡 結論與建議

### ✅ 最終決策：採用 Gemini 3 Flash

#### 優勢總結
| 維度 | Flash 表現 | 評級 |
|------|-----------|------|
| **速度** | 比 Pro 快 2.7 倍 | ⭐⭐⭐⭐⭐ |
| **品質** | 與 Pro 相同（5/5） | ⭐⭐⭐⭐⭐ |
| **成本** | 更經濟 | ⭐⭐⭐⭐⭐ |
| **可用性** | 免費額度充足 | ⭐⭐⭐⭐⭐ |

#### Pro 版本的問題
- ❌ 速度過慢（69 秒完整流程）
- ❌ 免費額度限制（測試中遇到 429 配額錯誤）
- ❌ 用戶體驗不佳（等待時間過長）

### 🎯 適用場景

#### Flash 最適合的場景（✅ 本專案）
- 實時健康數據處理
- 快速 OCR 辨識需求
- 個人化報告生成
- 對話式 AI 營養師

#### Pro 適合的場景（本專案不適用）
- 複雜推理任務
- 需要更長文本輸出
- 對延遲不敏感的批次處理

---

## 🔮 未來展望

### 短期優化（3 個月內）
1. **監控 Flash 性能**：持續追蹤速度與品質指標
2. **A/B 測試**：小範圍測試 Flash vs Pro 的真實用戶反饋
3. **成本分析**：計算每月 API 使用成本

### 長期規劃（6 個月以上）
1. **模型升級評估**：
   - Gemini 2.0 系列正式版發布後重新評估
   - 關注 Gemini 2.5 Pro 的性能提升
2. **混合策略**：
   - 簡單任務使用 Flash（OCR、Chat）
   - 複雜任務使用 Pro（深度分析報告）
3. **自建模型**：
   - 評估使用開源 LLM（Llama 3、Mistral）
   - 本地部署降低 API 成本

---

## 📚 參考資料

### 官方文檔
- [Google Gemini API 文檔](https://ai.google.dev/gemini-api/docs)
- [Gemini Models 比較](https://ai.google.dev/gemini-api/docs/models)
- [API 配額與限制](https://ai.google.dev/gemini-api/docs/rate-limits)

### 專案文檔
- [README.md](../README.md)：專案總覽
- [CHANGELOG.md](../CHANGELOG.md)：版本更新日誌
- [01_技術規格文件_MVP核心架構.md](../01_技術規格文件_MVP核心架構.md)：技術架構

### 測試相關
- [test_model_comparison.py](../test_model_comparison.py)：測試腳本原始碼
- [model_comparison_results.json](../model_comparison_results.json)：完整測試數據

---

## 📝 更新記錄

| 日期 | 版本 | 內容 |
|------|------|------|
| 2026-01-17 | v1.0 | 初始版本：Flash vs Pro 對比測試報告 |

---

**文檔維護者**：Personal Health 開發團隊  
**最後更新**：2026-01-17
