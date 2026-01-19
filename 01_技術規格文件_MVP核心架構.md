# Precise Personalized Health - MVP 技術規格文件

> **最後更新**：2026-01-17  
> **當前版本**：v1.2.0 - 已實現 Flutter 跨平台 App

## 系統狀態總覽

### ✅ 已實現功能
- **後端系統**：FastAPI + Gemini AI + OCR + 推薦引擎
- **Web 前端**：Streamlit 完整 UI
- **行動 App**：Flutter (iOS/Android/Windows) 核心功能完成
  - 個人資料管理（含表單驗證）
  - 健檢報告上傳（OCR 自動解析）
  - 健康儀表板（趨勢圖表 + AI 建議）
  - AI 對話助手（上下文理解 + UX 優化）
  - 環境配置系統（dev/staging/production）

---

## 文檔目標
本文檔定義從用戶輸入到營養建議輸出的完整數據流與處理架構，確保：
- 每個建議可解釋、可追溯、可被營養師稽核
- OCR 處理可控、錯誤可檢測
- 數據不足時能降級輸出而非失敗

---

## 一、整體架構概覽

```
輸入層 (Input Layer)
  ├── 基本資料 (Demographics)
  ├── 健檢報告 OCR (Lab Results)
  ├── 問答評估 (Questionnaire)
  └── 目標設定 (Goals)
         ↓
標準化層 (Normalization Layer)
  ├── 單位轉換
  ├── 信心評分
  └── 缺失檢測
         ↓
中間表示層 (Intermediate Representation)
  ├── Health Snapshot (健康狀態摘要)
  ├── Diet Targets (飲食目標)
  └── Nutrient Gaps (營養缺口)
         ↓
推薦引擎 (Recommendation Engine)
  ├── 決策層 (Rules + Scoring)
  └── 呈現層 (NLG + Templates)
         ↓
輸出層 (Output Layer)
  ├── 健康指數儀表板
  ├── 飲食建議 (情境化)
  ├── 食材清單
  └── 保健食品建議 (條件性)
         ↓
營養師覆核工作台 (Nutritionist Workbench)
```

---

## 二、輸入層數據規格與轉譯映射表

### 2.1 基本資料 (Demographics)

| 輸入欄位 | 數據類型 | 必填 | 標準化後欄位 | 備註 |
|---------|---------|-----|------------|-----|
| 性別 | enum | 是 | gender | male/female/other |
| 年齡 | number | 是 | age | 單位：歲 |
| 身高 | number | 是 | height_cm | 單位：cm |
| 體重 | number | 是 | weight_kg | 單位：kg |
| 活動量 | enum | 是 | activity_level | sedentary/light/moderate/high |
| 飲食型態 | enum | 否 | diet_type | general/vegetarian/low_carb/etc |
| 過敏史 | text[] | 否 | allergies | 自由輸入，需後續標準化 |
| 懷孕/哺乳 | boolean | 是 | is_pregnant_lactating | 高風險分流條件 |

**衍生特徵 (Derived Features):**
- `bmi = weight_kg / (height_cm/100)^2`
- `bmi_category` (underweight/normal/overweight/obese)
- `age_group` (18-30/31-45/46-60/60+)

---

### 2.2 健檢報告 OCR (Lab Results)

#### MVP 優先支援的 15 個核心指標

| 檢驗項目 | 標準化欄位名 | 單位選項 | 參考範圍 (示例) | 用途 |
|---------|------------|---------|---------------|-----|
| 空腹血糖 | glucose_fasting | mg/dL, mmol/L | 70-100 mg/dL | 代謝評估 |
| 糖化血色素 | hba1c | % | 4.0-5.6% | 代謝評估 |
| 總膽固醇 | cholesterol_total | mg/dL, mmol/L | <200 mg/dL | 血脂評估 |
| 低密度脂蛋白 | ldl | mg/dL, mmol/L | <130 mg/dL | 血脂評估 |
| 高密度脂蛋白 | hdl | mg/dL, mmol/L | >40 mg/dL (男) | 血脂評估 |
| 三酸甘油脂 | triglycerides | mg/dL, mmol/L | <150 mg/dL | 血脂評估 |
| 谷丙轉氨酶 | alt | U/L | 0-40 U/L | 肝功能 |
| 谷草轉氨酶 | ast | U/L | 0-40 U/L | 肝功能 |
| 肌酸酐 | creatinine | mg/dL, μmol/L | 0.6-1.2 mg/dL | 腎功能 |
| 尿酸 | uric_acid | mg/dL, μmol/L | 3.5-7.2 mg/dL | 代謝評估 |
| 血紅素 | hemoglobin | g/dL | 12-16 g/dL (女) | 貧血評估 |
| 維生素D | vitamin_d | ng/mL, nmol/L | 30-100 ng/mL | 營養狀態 |
| 維生素B12 | vitamin_b12 | pg/mL, pmol/L | 200-900 pg/mL | 營養狀態 |
| 鐵蛋白 | ferritin | ng/mL, μg/L | 12-150 ng/mL (女) | 鐵儲存 |
| 葉酸 | folate | ng/mL, nmol/L | >3 ng/mL | 營養狀態 |

#### OCR 輸出數據結構 (JSON Schema)

```json
{
  "lab_results": [
    {
      "test_name": "glucose_fasting",
      "value": 95.0,
      "unit": "mg/dL",
      "ref_range": {
        "low": 70,
        "high": 100,
        "unit": "mg/dL"
      },
      "test_date": "2026-01-10",
      "ocr_confidence": 0.92,
      "status": "confirmed",  // confirmed / needs_review / rejected
      "evidence_location": {
        "page": 1,
        "bbox": [120, 340, 280, 365]
      },
      "validation_flags": []  // empty 表示通過校驗
    }
  ],
  "report_metadata": {
    "lab_name": "台北某某檢驗所",
    "report_date": "2026-01-10",
    "ocr_processing_version": "v1.2.0"
  }
}
```

#### OCR 校驗規則 (Validation Rules)

| 校驗類型 | 規則 | 觸發條件 | 處理方式 |
|---------|-----|---------|---------|
| 合理範圍檢查 | value 在生理可能範圍內 | 超出 0.1x - 10x 參考範圍 | 標記 needs_review |
| 單位一致性 | 同一報告單位系統一致 | 混用不同單位系統 | 標記 needs_review |
| 參考範圍對齊 | ref_range 與 value 單位匹配 | 單位不匹配 | 自動轉換或標記 |
| 低信心欄位 | ocr_confidence < 0.75 | 低信心 | 要求用戶確認 |
| 缺失關鍵欄位 | 缺少 value/unit/ref_range | 抽取不完整 | 標記 needs_review |

---

### 2.3 問答評估 (Questionnaire)

#### 2.3.1 飲食習慣評估

| 問題 | 欄位名 | 數據類型 | 映射到營養素 Proxy |
|-----|-------|---------|------------------|
| 每日蔬菜份數 | veg_servings_per_day | number (0-5+) | fiber, folate, vitamins |
| 每周魚類次數 | fish_per_week | number (0-7+) | omega-3, vitamin_d, protein |
| 每周紅肉次數 | red_meat_per_week | number (0-7+) | iron, b12, protein |
| 每日水果份數 | fruit_servings_per_day | number (0-3+) | vitamin_c, fiber |
| 乳製品攝取 | dairy_frequency | enum (never/rarely/sometimes/daily) | calcium, vitamin_d, b12 |
| 全穀雜糧 | whole_grain_frequency | enum (never/rarely/sometimes/daily) | fiber, b_vitamins, magnesium |
| 外食頻率 | eating_out_frequency | number (0-21 餐/周) | 用於評估控制難度 |
| 便利商店頻率 | convenience_store_freq | number (0-21 餐/周) | 情境化建議觸發 |
| 含糖飲料 | sugary_drinks_per_week | number (0-14+) | 代謝風險因子 |
| 飲水量 | water_intake_ml | number | hydration |

#### 2.3.2 生活型態評估

| 問題 | 欄位名 | 數據類型 | 用途 |
|-----|-------|---------|-----|
| 睡眠時數 | sleep_hours_avg | number (4-10) | 健康指數、壓力評估 |
| 壓力程度 | stress_level | scale (1-5) | 健康指數 |
| 運動頻率 | exercise_per_week | number (0-7+) | 活動量校正、目標設定 |
| 久坐時數 | sitting_hours_per_day | number (0-16) | 代謝風險因子 |
| 吸菸 | smoking_status | enum (never/former/current) | 風險分流 |
| 飲酒 | alcohol_frequency | enum (never/occasional/regular) | 肝功能、營養吸收 |

#### 2.3.3 健康史 (非藥物，僅用於飲食建議調整)

| 問題 | 欄位名 | 數據類型 | 用途 |
|-----|-------|---------|-----|
| 消化問題 | digestive_issues | text[] (便秘/腹瀉/脹氣/etc) | 纖維、益生菌建議調整 |
| 肌膚狀況 | skin_condition | text[] (乾燥/痘痘/etc) | omega-3, vitamins 建議 |
| 精神狀態 | energy_level | scale (1-5) | b_vitamins, iron 評估 |
| 經期狀況 (女性) | menstrual_regularity | enum (regular/irregular/none) | iron, folate 需求評估 |

---

### 2.4 目標設定 (Goals)

| 目標類型 | 欄位名 | 影響的 Targets |
|---------|-------|---------------|
| 減重 | goal_weight_loss | 降低熱量、提高蛋白質比例、增加纖維 |
| 增肌 | goal_muscle_gain | 提高熱量、高蛋白質、運動後營養 |
| 改善體質 | goal_general_health | 平衡營養、微量素補足 |
| 改善精神 | goal_energy | b_vitamins, iron, 睡眠飲食調整 |
| 腸道健康 | goal_gut_health | 纖維、益生元、發酵食物 |
| 皮膚改善 | goal_skin | omega-3, vitamins A/C/E |

---

## 三、中間表示層 (Intermediate Representation)

### 3.1 Health Snapshot (健康狀態摘要)

**數據結構:**

```json
{
  "snapshot_id": "uuid",
  "user_id": "uuid",
  "created_at": "2026-01-16T10:30:00Z",
  "data_completeness": 0.78,  // 0-1, 資料完整度
  "overall_confidence": 0.72,  // 0-1, 整體信心分數
  
  "indices": {
    "metabolic_index": {
      "score": 0.68,  // 0-1, 1=最佳
      "level": "moderate_risk",  // optimal/good/moderate_risk/high_risk
      "derived_from": ["glucose_fasting", "hba1c", "bmi", "triglycerides"],
      "missing_inputs": ["hba1c"],
      "confidence": 0.65
    },
    "cardiovascular_index": {
      "score": 0.72,
      "level": "good",
      "derived_from": ["cholesterol_total", "ldl", "hdl", "triglycerides", "blood_pressure"],
      "missing_inputs": ["blood_pressure"],
      "confidence": 0.70
    },
    "liver_kidney_index": {
      "score": 0.85,
      "level": "optimal",
      "derived_from": ["alt", "ast", "creatinine"],
      "missing_inputs": [],
      "confidence": 0.90
    },
    "nutrition_status_index": {
      "score": 0.55,
      "level": "needs_attention",
      "derived_from": ["hemoglobin", "vitamin_d", "ferritin", "diet_questionnaire"],
      "missing_inputs": ["vitamin_b12", "folate"],
      "confidence": 0.60
    },
    "lifestyle_index": {
      "score": 0.60,
      "level": "moderate",
      "derived_from": ["sleep_hours_avg", "stress_level", "exercise_per_week", "sitting_hours"],
      "missing_inputs": [],
      "confidence": 0.80
    }
  },
  
  "risk_flags": [
    {
      "type": "high_risk_pregnancy",
      "triggered": false
    },
    {
      "type": "kidney_function_concern",
      "triggered": false
    },
    {
      "type": "liver_function_concern",
      "triggered": false
    },
    {
      "type": "severe_anemia",
      "triggered": false
    }
  ]
}
```

---

### 3.2 Diet Targets (飲食目標)

根據用戶基本資料、活動量、目標計算出的每日營養目標。

**數據結構:**

```json
{
  "targets_id": "uuid",
  "user_id": "uuid",
  "goal": "weight_loss",  // 或 muscle_gain, general_health
  "created_at": "2026-01-16T10:30:00Z",
  
  "macronutrients": {
    "calories": {
      "target_kcal": 1600,
      "range": [1500, 1700],
      "calculation_method": "Mifflin-St Jeor * activity_factor * goal_adjustment",
      "confidence": 0.85
    },
    "protein": {
      "target_g": 100,
      "target_g_per_kg": 1.5,
      "range": [90, 110],
      "priority": "high",
      "reason": "增肌目標 + 減重期保持肌肉量"
    },
    "carbohydrates": {
      "target_g": 160,
      "range": [140, 180],
      "priority": "medium"
    },
    "fat": {
      "target_g": 53,
      "range": [45, 60],
      "priority": "medium"
    },
    "fiber": {
      "target_g": 28,
      "range": [25, 30],
      "priority": "high",
      "reason": "飽足感 + 腸道健康"
    },
    "water": {
      "target_ml": 2000,
      "range": [1800, 2500]
    }
  },
  
  "micronutrients_of_concern": [
    {
      "nutrient": "iron",
      "target_mg": 18,
      "priority": "high",
      "reason": "女性 + 可能缺乏指標"
    },
    {
      "nutrient": "calcium",
      "target_mg": 1000,
      "priority": "medium",
      "reason": "乳製品攝取不足"
    },
    {
      "nutrient": "vitamin_d",
      "target_iu": 800,
      "priority": "high",
      "reason": "檢驗值偏低"
    }
  ],
  
  "meal_distribution": {
    "meals_per_day": 3,
    "snacks_per_day": 1,
    "protein_per_meal_g": 33,
    "veg_servings_per_day": 3
  },
  
  "constraints": [
    "no_cooking",
    "frequent_convenience_store",
    "lactose_intolerance"
  ]
}
```

---

### 3.3 Nutrient Gaps (營養缺口)

對比 Diet Targets 與 當前攝取估計值 (從問卷推估)。

**數據結構:**

```json
{
  "gaps_id": "uuid",
  "user_id": "uuid",
  "created_at": "2026-01-16T10:30:00Z",
  
  "gaps": [
    {
      "nutrient": "protein",
      "target_value": 100,
      "current_estimate": 65,
      "gap_percentage": -35,
      "gap_score": 0.82,  // 0-1, 越高表示缺口越明顯
      "confidence": 0.70,
      "evidence": [
        {"source": "diet_questionnaire", "indicator": "red_meat_per_week", "value": 1},
        {"source": "diet_questionnaire", "indicator": "fish_per_week", "value": 0},
        {"source": "goal", "indicator": "muscle_gain", "value": true}
      ],
      "priority": "high",
      "recommendation_trigger": "diet_first"
    },
    {
      "nutrient": "fiber",
      "target_value": 28,
      "current_estimate": 12,
      "gap_percentage": -57,
      "gap_score": 0.95,
      "confidence": 0.85,
      "evidence": [
        {"source": "diet_questionnaire", "indicator": "veg_servings_per_day", "value": 1},
        {"source": "diet_questionnaire", "indicator": "whole_grain_frequency", "value": "rarely"}
      ],
      "priority": "critical",
      "recommendation_trigger": "diet_first"
    },
    {
      "nutrient": "vitamin_d",
      "target_value": 800,
      "current_estimate": null,
      "gap_score": 0.88,
      "confidence": 0.65,
      "evidence": [
        {"source": "lab_result", "indicator": "vitamin_d", "value": 18, "unit": "ng/mL", "ref_low": 30},
        {"source": "diet_questionnaire", "indicator": "fish_per_week", "value": 0},
        {"source": "diet_questionnaire", "indicator": "dairy_frequency", "value": "rarely"}
      ],
      "priority": "high",
      "recommendation_trigger": "diet_and_supplement"  // 因為食物效率低
    },
    {
      "nutrient": "iron",
      "target_value": 18,
      "current_estimate": 9,
      "gap_percentage": -50,
      "gap_score": 0.75,
      "confidence": 0.60,
      "evidence": [
        {"source": "lab_result", "indicator": "hemoglobin", "value": 11.2, "unit": "g/dL", "ref_low": 12},
        {"source": "lab_result", "indicator": "ferritin", "value": 15, "unit": "ng/mL", "ref_low": 20},
        {"source": "diet_questionnaire", "indicator": "red_meat_per_week", "value": 1}
      ],
      "priority": "high",
      "recommendation_trigger": "diet_first",
      "safety_note": "若持續低下需排除其他原因，建議追蹤"
    }
  ],
  
  "summary": {
    "total_gaps": 4,
    "critical_gaps": 1,
    "high_priority_gaps": 3,
    "avg_confidence": 0.70
  }
}
```

---

## 四、推薦引擎 (Recommendation Engine)

### 4.1 架構：兩層引擎

```
決策層 (Decision Layer)
  ├── Rules Engine (規則引擎)
  │   ├── 安全門規則 (Safety Gates)
  │   ├── 分流規則 (Triage Rules)
  │   └── 優先級排序規則 (Prioritization)
  │
  └── Scoring Model (評分模型)
      ├── 缺口嚴重度
      ├── 可執行性
      └── 用戶偏好
          ↓
呈現層 (Presentation Layer)
  ├── Template Engine (情境化模板)
  └── NLG Layer (自然語言生成)
```

---

### 4.2 決策層輸出：結構化建議物件

**Recommendation Object Schema:**

```json
{
  "recommendation_id": "uuid",
  "user_id": "uuid",
  "created_at": "2026-01-16T10:30:00Z",
  "type": "diet_action",  // diet_action / food_item / supplement
  "category": "protein_boost",
  "priority_score": 0.92,
  
  "action": {
    "title": "每天至少 2 餐加入一份高蛋白主菜",
    "description": "目前蛋白質攝取約 65g/天，建議提升至 100g/天以支援增肌目標",
    "target_nutrient": ["protein"],
    "gap_addressed": {
      "nutrient": "protein",
      "gap_score": 0.82
    }
  },
  
  "execution": {
    "context_templates": ["convenience_store", "bento_shop", "breakfast_shop"],
    "serving_guidance": "每餐蛋白質至少一個手掌大小（約 30-35g）",
    "frequency": "daily",
    "meal_timing": ["lunch", "dinner"]
  },
  
  "alternatives": [
    {
      "option": "超商：茶葉蛋 2 顆 + 無糖豆漿",
      "protein_g": 35,
      "feasibility": "high"
    },
    {
      "option": "便當店：主菜換雞腿或魚片，加點滷蛋",
      "protein_g": 40,
      "feasibility": "high"
    },
    {
      "option": "早餐店：厚片土司 + 煎蛋 + 鮪魚",
      "protein_g": 30,
      "feasibility": "medium"
    }
  ],
  
  "evidence": [
    {
      "type": "nutrient_gap",
      "nutrient": "protein",
      "current": 65,
      "target": 100,
      "confidence": 0.70
    },
    {
      "type": "goal",
      "goal": "muscle_gain"
    },
    {
      "type": "constraint",
      "constraint": "no_cooking",
      "影響": "需提供外食方案"
    }
  ],
  
  "safety_notes": [],
  "contraindications": [],
  
  "confidence": 0.75,
  "version": "recommendation_engine_v1.0"
}
```

---

### 4.3 補充品建議的觸發條件（升級條件）

補充品建議採用**保守觸發策略**，需同時滿足：

| 條件類別 | 具體條件 | 說明 |
|---------|---------|-----|
| **安全門通過** | 無高風險旗標 | 孕哺、腎肝異常、多重用藥等直接阻斷 |
| **缺口顯著** | gap_score >= 0.75 | 且 confidence >= 0.6 |
| **食物效率低** | 至少符合一項：<br>1. 外食頻率 > 14餐/周<br>2. 特定營養素（如維生素D）食物來源有限<br>3. 用戶明確偏好補充方案 | 避免"一缺就推" |
| **已給飲食方案** | 必須先輸出飲食建議 | 補充品不能單獨出現 |

**觸發邏輯 (偽代碼):**

```python
def should_recommend_supplement(gap, user_profile, health_snapshot):
    # 安全門
    if any(health_snapshot.risk_flags.triggered):
        return False
    
    # 缺口與信心
    if gap.gap_score < 0.75 or gap.confidence < 0.6:
        return False
    
    # 食物效率評估
    food_efficiency_low = (
        user_profile.eating_out_frequency > 14 or
        gap.nutrient in LOW_FOOD_EFFICIENCY_NUTRIENTS or
        user_profile.prefers_supplement
    )
    
    if not food_efficiency_low:
        return False
    
    # 必須已有飲食建議
    if not has_diet_recommendation_for(gap.nutrient):
        return False
    
    return True

LOW_FOOD_EFFICIENCY_NUTRIENTS = ["vitamin_d", "omega_3", "specific_minerals"]
```

---

### 4.4 補充品建議輸出格式

```json
{
  "recommendation_id": "uuid",
  "type": "supplement",
  "category": "vitamin_d",
  "priority_score": 0.88,
  
  "supplement": {
    "ingredient": "vitamin_d3",
    "dosage": "800-1000 IU",
    "frequency": "daily",
    "duration": "持續性，建議 8-12 周後複檢",
    "form": "軟膠囊或滴劑"
  },
  
  "rationale": {
    "primary_reason": "檢驗值 18 ng/mL (參考範圍 30-100)，食物來源有限",
    "gap_score": 0.88,
    "confidence": 0.65,
    "evidence_summary": "檢驗數據 + 飲食評估 + 日照不足"
  },
  
  "diet_alternative": {
    "description": "每周至少 2 次富含脂肪魚類（鯖魚、鮭魚）+ 每日強化乳品",
    "feasibility": "medium",
    "estimated_intake": "約 400-600 IU/天（仍不足）"
  },
  
  "safety_info": {
    "max_daily_dose": "4000 IU (UL)",
    "contraindications": ["高鈣血症", "腎結石病史"],
    "interactions": ["某些心臟藥物需諮詢醫師"],
    "monitoring": "建議 3 個月後複檢血中濃度"
  },
  
  "product_criteria": {
    "must_have": ["vitamin_d3 形式", "劑量 800-1000 IU", "食品級認證"],
    "preferred": ["第三方檢測", "無不必要添加物"],
    "避免": ["超高劑量（>2000 IU 單次）", "複方過度"]
  },
  
  "confidence": 0.65,
  "requires_nutritionist_review": false,
  "version": "recommendation_engine_v1.0"
}
```

---

## 五、OCR 處理流程詳細規格

### 5.1 處理管線 (Pipeline)

```
用戶上傳檢驗報告照片
    ↓
Step 1: 圖像預處理
  - 旋轉校正
  - 去噪
  - 對比增強
    ↓
Step 2: OCR 抽取
  - 表格結構識別
  - 文字識別（項目名、數值、單位、參考範圍）
    ↓
Step 3: 欄位抽取與映射
  - 識別檢驗項目 → 映射到標準欄位名
  - 抽取數值、單位、參考範圍
    ↓
Step 4: 校驗 (Validation)
  - 合理範圍檢查
  - 單位一致性檢查
  - 參考範圍對齊檢查
  - 信心分數計算
    ↓
Step 5: 確認介面
  - 低信心欄位 → 要求用戶確認
  - 異常值 → 標記警告
  - 缺失欄位 → 提示手動輸入
    ↓
Step 6: 結構化儲存
  - 存入 lab_results 表
  - 保留原始抽取結果與確認紀錄
  - 記錄 OCR 版本與處理時間
```

---

### 5.2 欄位抽取映射表 (Field Mapping)

**常見檢驗項目名稱變體 → 標準欄位名**

| 標準欄位名 | 可能出現的名稱變體 | 單位變體 |
|-----------|------------------|---------|
| glucose_fasting | 空腹血糖, 飯前血糖, AC Sugar, Fasting Glucose | mg/dL, mmol/L |
| hba1c | 糖化血色素, 糖化血紅蛋白, HbA1c, Glycated Hemoglobin | % |
| cholesterol_total | 總膽固醇, 膽固醇, T-CHO, Total Cholesterol | mg/dL, mmol/L |
| ldl | 低密度脂蛋白, LDL-C, LDL Cholesterol | mg/dL, mmol/L |
| hdl | 高密度脂蛋白, HDL-C, HDL Cholesterol | mg/dL, mmol/L |
| triglycerides | 三酸甘油脂, 三酸甘油酯, TG, Triglyceride | mg/dL, mmol/L |
| alt | 谷丙轉氨酶, GPT, ALT, SGPT | U/L, IU/L |
| ast | 谷草轉氨酶, GOT, AST, SGOT | U/L, IU/L |
| creatinine | 肌酸酐, 肌酐, Cre, Creatinine | mg/dL, μmol/L |
| uric_acid | 尿酸, UA, Uric Acid | mg/dL, μmol/L |

**實現建議：**
- 建立 `field_name_variants` 表，支援模糊匹配
- 使用 NLP 相似度算法輔助映射
- 支援人工標註與機器學習持續優化

---

### 5.3 單位轉換表

| 檢驗項目 | 從單位 | 到單位 (標準) | 轉換公式 |
|---------|-------|-------------|---------|
| glucose_fasting | mmol/L | mg/dL | mg/dL = mmol/L × 18.02 |
| cholesterol_total | mmol/L | mg/dL | mg/dL = mmol/L × 38.67 |
| creatinine | μmol/L | mg/dL | mg/dL = μmol/L ÷ 88.4 |
| uric_acid | μmol/L | mg/dL | mg/dL = μmol/L ÷ 59.48 |

---

### 5.4 校驗規則詳細定義

#### 規則 1: 合理範圍檢查 (Physiological Range Check)

| 檢驗項目 | 最小可能值 | 最大可能值 | 觸發條件 |
|---------|-----------|-----------|---------|
| glucose_fasting | 30 mg/dL | 400 mg/dL | 超出範圍標記 needs_review |
| cholesterol_total | 50 mg/dL | 500 mg/dL | 同上 |
| alt | 0 U/L | 500 U/L | 同上 |
| creatinine | 0.2 mg/dL | 15 mg/dL | 同上 |

#### 規則 2: 單位-參考範圍一致性檢查

```python
def validate_unit_ref_consistency(lab_result):
    value_unit = lab_result.unit
    ref_unit = lab_result.ref_range.unit
    
    if value_unit != ref_unit:
        # 嘗試自動轉換
        converted = convert_unit(lab_result.value, value_unit, ref_unit)
        if converted:
            lab_result.value = converted
            lab_result.unit = ref_unit
            lab_result.validation_flags.append("unit_auto_converted")
        else:
            lab_result.status = "needs_review"
            lab_result.validation_flags.append("unit_mismatch")
```

#### 規則 3: 低信心閾值

```python
CONFIDENCE_THRESHOLD = 0.75

if lab_result.ocr_confidence < CONFIDENCE_THRESHOLD:
    lab_result.status = "needs_review"
    lab_result.validation_flags.append("low_ocr_confidence")
```

---

### 5.5 確認介面 UX 流程

用戶上傳後看到：

```
✓ 已成功識別 12 個檢驗項目
⚠ 2 個項目需要您確認

[需確認項目 1]
檢驗項目: 空腹血糖
識別結果: 95 mg/dL
參考範圍: 70-100 mg/dL
信心度: 72%

[確認] [修改] [刪除此項]

[需確認項目 2]  
檢驗項目: 維生素D
識別結果: 1? ng/mL (數字不清楚)
參考範圍: 30-100 ng/mL

請手動輸入: [ _ _ ] ng/mL

[確認全部] 按鈕
```

---

## 六、安全門與降級策略

### 6.1 風險分流規則 (Triage Rules)

| 風險等級 | 觸發條件 | 輸出限制 |
|---------|---------|---------|
| **高風險** | - 懷孕/哺乳<br>- 腎功能異常 (Cr > 1.5)<br>- 肝功能異常 (ALT/AST > 2x ULN)<br>- 未成年 (<18歲)<br>- 高齡 (>70歲) | - 禁止補充品建議<br>- 僅給一般飲食建議<br>- 明確提示"需諮詢專業人員" |
| **中風險** | - 單一慢性病指標偏高<br>- BMI < 18.5 or > 30<br>- 多個健檢數據缺失 | - 限制補充品種類（僅低風險品項）<br>- 降低建議強度<br>- 增加追蹤提示 |
| **低風險** | - 一般健康優化需求<br>- 資料完整度 > 70%<br>- 無明顯健康警訊 | - 可給完整建議（飲食 + 補充品）<br>- 根據缺口提供個性化方案 |

**實現 (偽代碼):**

```python
def assess_risk_level(user_profile, health_snapshot, lab_results):
    if (
        user_profile.is_pregnant_lactating or
        user_profile.age < 18 or
        user_profile.age > 70 or
        any(lab.is_kidney_concern() for lab in lab_results) or
        any(lab.is_liver_concern() for lab in lab_results)
    ):
        return RiskLevel.HIGH
    
    if (
        user_profile.bmi < 18.5 or user_profile.bmi > 30 or
        health_snapshot.data_completeness < 0.5 or
        any(index.level == "high_risk" for index in health_snapshot.indices)
    ):
        return RiskLevel.MEDIUM
    
    return RiskLevel.LOW
```

---

### 6.2 補充品安全門規則

#### 成分黑名單（高風險族群）

| 族群/狀況 | 禁止推薦成分 | 原因 |
|---------|------------|-----|
| 懷孕/哺乳 | 高劑量維生素A, 某些草本 | 致畸風險 |
| 腎功能異常 | 高劑量鉀、磷、蛋白質補充劑 | 代謝負擔 |
| 高尿酸/痛風 | 高普林補充品、某些維生素B | 可能升高尿酸 |
| 凝血異常 | 高劑量維生素E、魚油（高劑量） | 增加出血風險 |

#### 劑量上限 (UL - Upper Limit)

| 成分 | 每日上限 (UL) | 保守建議劑量 |
|-----|-------------|------------|
| 維生素D | 4000 IU | 800-1000 IU |
| 鈣 | 2500 mg | 500-1000 mg |
| 鐵 | 45 mg | 18-27 mg (女性) |
| 魚油 (EPA+DHA) | 3000 mg | 1000-2000 mg |
| 維生素B6 | 100 mg | 2-10 mg |

**實現：堆疊計算**

```python
def check_dosage_stacking(recommended_supplements):
    """檢查多個補充品是否導致某成分超量"""
    ingredient_totals = {}
    
    for supp in recommended_supplements:
        for ingredient, dosage in supp.ingredients.items():
            ingredient_totals[ingredient] = ingredient_totals.get(ingredient, 0) + dosage
    
    violations = []
    for ingredient, total_dosage in ingredient_totals.items():
        ul = UPPER_LIMITS.get(ingredient)
        if ul and total_dosage > ul:
            violations.append({
                "ingredient": ingredient,
                "total": total_dosage,
                "limit": ul
            })
    
    return violations
```

---

### 6.3 降級策略 (Degradation Policy)

當資料不足或風險高時，系統自動降級輸出：

| 情境 | 原本輸出 | 降級後輸出 |
|-----|---------|-----------|
| 健檢數據全缺 | 精準營養缺口 | 基於問卷的一般建議 + "補充檢驗數據可更精準" |
| OCR 信心低 | 直接使用數據推論 | 標記不確定性 + 要求確認 |
| 高風險族群 | 補充品建議 | 僅飲食建議 + "請諮詢營養師/醫師" |
| 目標衝突 | 單一最佳方案 | 提供多種情境方案，讓營養師選擇 |

---

## 七、營養師覆核工作台

### 7.1 工作台核心功能

#### 功能 1: 一頁式案例摘要 (Case Summary)

**顯示內容：**
- **用戶基本資料**: 年齡、性別、BMI、目標
- **風險旗標**: 高亮顯示任何高風險因子
- **資料完整度**: 78% (缺少：血壓、維生素B12)
- **健康指數儀表板**: 5 大指數一目了然
- **Top 3 營養缺口**: fiber (-57%), protein (-35%), vitamin_d (-?)
- **系統建議草案**: 3 條飲食建議 + 1 條補充品建議
- **置信度摘要**: 全體信心 72%

**操作按鈕：**
- [快速通過] - 信任系統建議，直接發佈
- [編輯建議] - 進入編輯模式
- [標記高風險/轉介] - 阻止發佈，轉人工深度諮詢

---

#### 功能 2: 建議編輯器

**支援操作：**
- 修改建議文字（保留原文對照）
- 調整優先級排序
- 新增/刪除建議項目
- 修改補充品劑量/週期
- 添加個性化注意事項

**版本控制：**
```json
{
  "recommendation_id": "uuid",
  "versions": [
    {
      "version": 1,
      "created_by": "system",
      "created_at": "2026-01-16T10:30:00Z",
      "content": "系統原始建議..."
    },
    {
      "version": 2,
      "created_by": "nutritionist_id_123",
      "created_at": "2026-01-16T11:05:00Z",
      "content": "營養師修改後...",
      "changes": "調整蛋白質目標從 100g → 90g，考慮用戶實際執行難度",
      "review_notes": "用戶外食頻率高，降低目標提高依從性"
    }
  ],
  "published_version": 2
}
```

---

#### 功能 3: 快速檢查清單 (Checklist)

營養師覆核時必檢查項目（系統自動標註狀態）：

- [ ] 風險分流正確（高風險族群未給補充品）
- [ ] 健檢數據已確認（無低信心未確認項目）
- [ ] 目標與建議一致（例如減重但未控制熱量）
- [ ] 補充品劑量保守（未超過 UL）
- [ ] 禁忌/交互作用已排除（系統自動，營養師複核）
- [ ] 飲食建議可執行（符合用戶限制）
- [ ] 文案無醫療宣稱（避免"治療"、"治癒"等詞）

---

### 7.2 稽核與追溯能力

**每次建議發佈後，系統自動記錄：**

```json
{
  "audit_log_id": "uuid",
  "recommendation_id": "uuid",
  "user_id": "uuid",
  "published_at": "2026-01-16T11:10:00Z",
  "published_by": "nutritionist_id_123",
  
  "snapshot_at_publication": {
    "input_data_version": "v1.0",
    "ocr_results_version": "v1.2.0",
    "recommendation_engine_version": "v1.0",
    "rules_version": "v2.3",
    "health_snapshot_id": "uuid",
    "diet_targets_id": "uuid",
    "nutrient_gaps_id": "uuid"
  },
  
  "review_metadata": {
    "review_duration_seconds": 320,
    "modifications_made": true,
    "checklist_completed": true,
    "risk_level_override": false
  },
  
  "user_feedback": {
    "viewed_at": "2026-01-16T14:20:00Z",
    "採納率": null,  // 後續追蹤
    "reported_issues": []
  }
}
```

**用途：**
- 事後復盤：任何客訴可完整重建當時決策依據
- 品質監控：追蹤營養師覆核時間、修改率、用戶滿意度
- 規則迭代：分析哪些系統建議常被修改，優化規則

---

## 八、MVP 開發優先級與驗收標準

### Phase 1: 核心數據流 (2-3 sprints)

| 模組 | 功能 | 驗收標準 |
|-----|------|---------|
| 輸入層 | 基本資料 + 問卷 | 能完整收集 Demographics + Questionnaire，存入標準化 schema |
| 中間層 | Health Snapshot | 能計算至少 3 個核心指數（metabolic, nutrition, lifestyle），顯示信心與缺失 |
| 中間層 | Diet Targets | 能根據目標（減重/增肌）計算基礎 macros 目標 |
| 中間層 | Nutrient Gaps | 能推估至少 5 個核心營養素缺口（protein, fiber, calcium, iron, vitamin_d） |

---

### Phase 2: OCR 管線 (2 sprints)

| 模組 | 功能 | 驗收標準 |
|-----|------|---------|
| OCR 抽取 | 健檢報告結構化 | 能穩定抽取 Top 10 檢驗項目，信心分數可計算 |
| 校驗 | 單位轉換 + 合理範圍檢查 | 異常值自動標記，低信心要求確認 |
| 確認介面 | 用戶二次確認 | 用戶能在 1 分鐘內完成確認流程 |

---

### Phase 3: 推薦引擎 (3-4 sprints)

| 模組 | 功能 | 驗收標準 |
|-----|------|---------|
| 決策層 | 規則引擎 | 能根據缺口生成結構化建議物件（至少飲食建議） |
| 決策層 | 安全門 | 高風險族群不出補充品建議 |
| 呈現層 | 情境化模板 | 至少支援 3 種情境（超商、便當、早餐店） |
| 呈現層 | 補充品建議 | 能依觸發條件輸出保守劑量建議，含安全資訊 |

---

### Phase 4: 營養師工作台 (2 sprints)

| 模組 | 功能 | 驗收標準 |
|-----|------|---------|
| 案例摘要 | 一頁式顯示 | 營養師能在 30 秒內掌握案例重點 |
| 編輯器 | 修改 + 版本控 | 能編輯建議，保留修改紀錄與理由 |
| 稽核 | Audit Log | 每次發佈自動記錄完整快照 |

---

### Phase 5: 品質監控 (1-2 sprints)

| 模組 | 功能 | 驗收標準 |
|-----|------|---------|
| 儀表板 | 營運指標 | 顯示：覆核時間、修改率、高風險比例、用戶採納率 |
| 回報機制 | 用戶反饋 + 不適回報 | 負面事件能自動標記，通知營養師 |

---

## 九、數據治理與合規（必備）

### 9.1 資料分級與最小化收集

| 資料類別 | 說明 | 預設保存 | 最小化原則 |
|---------|------|---------|-----------|
| 基本資料 | 年齡/性別/身高體重 | 是 | 僅保存用於計算目標的欄位 |
| 健檢影像 | 原始報告圖片 | 否（可選） | 預設只保留結構化數值，影像需用戶同意 |
| OCR 抽取結果 | 結構化檢驗值 | 是 | 僅保存必要指標與確認記錄 |
| 問卷/生活型態 | 飲食/睡眠/活動 | 是 | 僅保存與建議相關欄位 |

**原則：**
- 預設不保存原始影像；用戶選擇保存時應明確告知用途與保存期限。
- 明確顯示「提供越多資料 → 精準度提升」的差異說明。

### 9.2 存取權限與審計

| 角色 | 可訪問內容 | 限制 |
|------|-----------|------|
| 使用者 | 自身所有資料 | 可下載/可刪除 |
| 營養師 | 案例摘要 + 必要數據 | 不可下載原始影像（除非必要） |
| 管理員 | 系統維護與稽核 | 全程審計記錄 |

**審計要求：**
- 所有數據訪問需記錄：訪問者、時間、目的、涉及數據範圍。
- 營養師修改建議必須留存版本與理由（見 7.2）。

### 9.3 資料保存與刪除策略（Retention Policy）

| 資料類型 | 保存期限 | 刪除觸發 | 刪除方式 |
|---------|---------|---------|---------|
| 原始影像 | 預設不保存 | 用戶要求刪除 | 立即刪除 + 備份清除 |
| 結構化檢驗值 | 36 個月 | 用戶要求刪除 | 軟刪除 30 天 → 硬刪除 |
| 建議與覆核記錄 | 36 個月 | 法規或用戶要求 | 軟刪除 + 審計保留摘要 |
| 日誌/審計記錄 | 24 個月 | 到期自動清理 | 脫敏後歸檔 |

**備註：**以上期限依當地法規與業務需求調整。

---

## 十、食品營養資料庫（ODS）導入與維護

### 10.1 數據來源
- 檔案：食品營養成分資料庫2024UPDATE2.ods
- 僅「工作表1」含有效數據；工作表2/3為空
- 第 1 行為說明文字，真實欄位名從第 2 行開始

### 10.2 導入規則（ETL）

**讀取規則：**
- 讀取 `工作表1`
- 跳過第 1 行說明（`header=1`）
- 允許缺值（NaN）保留為 NULL
- 單位基準：每 100g 可食部分

**核心主鍵：**
- `整合編號` 作為 Food 主鍵

### 10.3 推薦用數據表設計（正規化）

**food_items（主表）**
```sql
CREATE TABLE food_items (
  food_id VARCHAR(20) PRIMARY KEY,  -- 整合編號
  category VARCHAR(100),            -- 食品分類
  name VARCHAR(200),                -- 樣品名稱
  alias VARCHAR(200),               -- 俗名
  description TEXT,                 -- 內容物描述
  refuse_rate_percent NUMERIC(6,2)  -- 廢棄率(%), 可為 NULL
);
```

**food_nutrients（明細表）**
```sql
CREATE TABLE food_nutrients (
  food_id VARCHAR(20) REFERENCES food_items(food_id),
  nutrient_key VARCHAR(100),         -- 例如 protein_g, vitamin_d_iu
  nutrient_value NUMERIC(12,4),
  unit VARCHAR(20),                  -- g, mg, ug, IU
  basis VARCHAR(50) DEFAULT 'per_100g',
  PRIMARY KEY (food_id, nutrient_key)
);
```

### 10.4 關鍵欄位映射（示例）

| ODS 欄位 | nutrient_key | unit |
|---------|--------------|------|
| 粗蛋白(g) | protein_g | g |
| 粗脂肪(g) | fat_g | g |
| 總碳水化合物(g) | carbs_g | g |
| 膳食纖維(g) | fiber_g | g |
| 維生素D總量(IU) | vitamin_d_iu | IU |
| 維生素B12(ug) | vitamin_b12_ug | ug |
| 葉酸(ug) | folate_ug | ug |
| 鈣(mg) | calcium_mg | mg |
| 鐵(mg) | iron_mg | mg |
| 鉀(mg) | potassium_mg | mg |
| 鈉(mg) | sodium_mg | mg |

### 10.5 更新機制

| 項目 | 頻率 | 方式 |
|-----|------|------|
| 原始資料庫更新 | 依官方發佈 | 人工下載 → ETL 導入 |
| 食品別名維護 | 每月 | 運營補充 + 營養師審核 |
| 數據質量檢查 | 每次導入 | 主鍵重複/異常值/單位檢查 |

---

## 十一、技術棧建議

| 層級 | 技術選項 | 說明 |
|-----|---------|-----|
| **OCR** | Azure Form Recognizer / Google Document AI / Tesseract + 自訓練模型 | 需支援繁體中文 + 表格結構 |
| **後端** | Python (FastAPI) / Node.js (NestJS) | FastAPI 適合 ML 整合 |
| **規則引擎** | Python Rules Engine (business-rules) / Drools | 需版本化與可解釋 |
| **數據庫** | PostgreSQL (關聯數據) + Redis (快取) | 需支援 JSON 欄位儲存複雜結構 |
| **NLG/LLM** | OpenAI GPT-4 / Claude / 自建模型 | 僅用於呈現層，不做決策 |
| **前端** | React / Vue.js | 需支援複雜表單與圖表 |
| **營養資料庫** | 台灣食品營養資料庫 API + 自建擴充 | 需本地化維護 |

---

## 十二、下一步行動建議

### 立即可做（本周）

1. **確認 MVP 目標族群**：先做"減重"還是"增肌"？影響 Diet Targets 計算優先級
2. **定義 Top 15 健檢指標**：哪些是 MVP 必須支援的
3. **收集 20-30 份真實健檢報告**：用於 OCR 訓練與測試
4. **建立第一版 Field Mapping 表**：檢驗項目名稱變體 → 標準欄位

### 2-4 周內

5. **開發 OCR 抽取 + 校驗 Pipeline**：先用現成 API，驗證可行性
6. **建立數據庫 Schema**：至少完成 Input Layer + IR Layer 的表結構
7. **實現第一版 Health Snapshot 計算**：3 個核心指數即可
8. **設計營養師工作台原型**：用 Figma 或直接低保真 UI

### 1-2 個月內

9. **完成 Nutrient Gaps 推估引擎**：含信心分數與降級邏輯
10. **開發推薦引擎 MVP**：至少能輸出 3 條飲食建議
11. **內部測試**：營養師團隊試用，收集反饋優化流程
12. **準備 10 個測試案例**：涵蓋低/中/高風險，驗證安全門有效性

---

## 附錄 A: 關鍵數據表 Schema (簡化版)

### users 表
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    gender VARCHAR(10),
    age INT,
    height_cm NUMERIC(5,2),
    weight_kg NUMERIC(5,2),
    activity_level VARCHAR(20),
    diet_type VARCHAR(50),
    is_pregnant_lactating BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### lab_results 表
```sql
CREATE TABLE lab_results (
    result_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    test_name VARCHAR(100),  -- 標準化欄位名
    value NUMERIC(10,3),
    unit VARCHAR(20),
    ref_low NUMERIC(10,3),
    ref_high NUMERIC(10,3),
    test_date DATE,
    ocr_confidence NUMERIC(3,2),
    status VARCHAR(20),  -- confirmed / needs_review / rejected
    validation_flags JSONB,
    created_at TIMESTAMP
);
```

### health_snapshots 表
```sql
CREATE TABLE health_snapshots (
    snapshot_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    data_completeness NUMERIC(3,2),
    overall_confidence NUMERIC(3,2),
    indices JSONB,  -- 儲存所有指數
    risk_flags JSONB,
    created_at TIMESTAMP
);
```

### recommendations 表
```sql
CREATE TABLE recommendations (
    recommendation_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    type VARCHAR(50),  -- diet_action / supplement
    priority_score NUMERIC(3,2),
    content JSONB,  -- 完整 recommendation object
    published_version INT,
    published_by UUID,  -- nutritionist_id
    published_at TIMESTAMP,
    created_at TIMESTAMP
);
```

---

## 附錄 B: 安全門規則配置範例 (YAML)

```yaml
safety_gates:
  high_risk_conditions:
    - condition: is_pregnant_lactating == true
      action: block_all_supplements
      message: "懷孕/哺乳期，建議由營養師個別評估"
    
    - condition: age < 18
      action: block_all_supplements
      message: "未成年用戶，僅提供飲食建議"
    
    - condition: creatinine > 1.5
      action: block_all_supplements
      message: "腎功能指標異常，請諮詢醫師後再考慮補充品"
    
    - condition: alt > 80 OR ast > 80
      action: block_all_supplements
      message: "肝功能指標偏高，建議先諮詢專業人員"

  supplement_dosage_limits:
    vitamin_d:
      max_daily_iu: 2000
      conservative_iu: 1000
      ul_iu: 4000
    
    calcium:
      max_daily_mg: 1000
      conservative_mg: 500
      ul_mg: 2500
    
    iron:
      max_daily_mg: 27
      conservative_mg: 18
      ul_mg: 45

  contraindications:
    - ingredient: high_dose_vitamin_a
      contraindicated_for: [pregnant, lactating]
    
    - ingredient: high_dose_fish_oil
      contraindicated_for: [bleeding_disorder, anticoagulant_user]
```

---

**文檔版本**: v1.0  
**最後更新**: 2026-01-16  
**維護者**: 產品/技術團隊  
**審核者**: 營養師團隊

