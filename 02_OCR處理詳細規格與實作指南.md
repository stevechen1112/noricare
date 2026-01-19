# OCR 健檢報告處理 - 詳細規格與實作指南

## 文檔目標
為 RD 提供完整的 OCR 處理流程規格，確保健檢報告數據抽取的**精準度**與**可控性**。

---

## 一、核心設計原則

### 1.1 優先級排序
1. **安全優先於便利**：寧可要求用戶確認，不要用錯誤數據推論
2. **可追溯優先於自動化**：每次抽取都要能複盤
3. **保守優先於激進**：低信心直接標記，不要硬推

### 1.2 成功標準
- ✅ 關鍵欄位抽取準確率 > 95%（經用戶確認後）
- ✅ 低信心欄位 100% 要求用戶確認
- ✅ 異常值 100% 被標記
- ✅ 每次抽取可追溯到原始圖像位置

---

## 二、健檢報告特性分析

### 2.1 台灣常見健檢報告類型

| 報告來源 | 版面特性 | 挑戰點 |
|---------|---------|-------|
| 醫院檢驗科 | 標準表格，清晰 | 不同醫院格式差異大 |
| 健檢中心 | 彩色、圖表豐富 | 版面複雜，需結構化識別 |
| 診所 | 簡易列表 | 字體小、手寫備註 |
| 自助檢測儀 | 熱感應紙、照片 | 對比度低、可能模糊 |

### 2.2 欄位分佈特性

**典型健檢報告結構：**
```
┌─────────────────────────────────────┐
│  XX 醫院檢驗報告                      │
│  姓名: XXX   性別: X   年齡: XX      │
│  檢驗日期: 2026/01/10                │
├─────────────────────────────────────┤
│ 檢驗項目     │  結果  │ 單位 │ 參考範圍 │
├─────────────────────────────────────┤
│ 空腹血糖     │  95   │ mg/dL│ 70-100  │
│ 總膽固醇     │  220  │ mg/dL│ <200    │
│ ALT(GPT)    │  42   │ U/L  │ 0-40    │
│ ...         │  ...  │ ...  │ ...     │
└─────────────────────────────────────┘
```

**欄位識別難點：**
- 項目名稱有多種寫法（空腹血糖 / 飯前血糖 / Fasting Glucose）
- 參考範圍格式不一（"70-100" / "<100" / "70~100"）
- 單位可能缺失或在不同位置
- 可能有手寫標註或印章遮擋

---

## 三、OCR 處理管線詳細設計

### 3.1 Pipeline 架構

```
[用戶上傳圖片]
     ↓
┌──────────────────────────────────┐
│ Stage 1: 圖像預處理               │
│  - 格式檢查 (JPG/PNG/PDF)         │
│  - 旋轉校正                       │
│  - 去噪與增強                     │
│  - 版面分析                       │
└──────────────────────────────────┘
     ↓
┌──────────────────────────────────┐
│ Stage 2: OCR 識別                │
│  - 表格結構檢測                   │
│  - 文字識別 (繁體中文 + 英數)     │
│  - 置信度計算                     │
└──────────────────────────────────┘
     ↓
┌──────────────────────────────────┐
│ Stage 3: 欄位抽取與標準化         │
│  - 項目名稱映射                   │
│  - 數值抽取與類型檢查             │
│  - 單位識別與轉換                 │
│  - 參考範圍解析                   │
└──────────────────────────────────┘
     ↓
┌──────────────────────────────────┐
│ Stage 4: 驗證 (Validation)       │
│  - 合理範圍檢查                   │
│  - 單位一致性檢查                 │
│  - 低信心標記                     │
│  - 缺失欄位檢測                   │
└──────────────────────────────────┘
     ↓
┌──────────────────────────────────┐
│ Stage 5: 用戶確認介面             │
│  - 顯示抽取結果                   │
│  - 高亮需確認項目                 │
│  - 提供修改/刪除/確認操作         │
└──────────────────────────────────┘
     ↓
┌──────────────────────────────────┐
│ Stage 6: 結構化儲存               │
│  - 存入 lab_results 表            │
│  - 保留原始圖像與抽取元數據       │
│  - 記錄處理版本                   │
└──────────────────────────────────┘
```

---

## 四、Stage 1: 圖像預處理

### 4.1 格式檢查與轉換

**支援格式：**
- 圖片：JPG, PNG, HEIC
- 文檔：PDF (單頁或多頁)

**處理流程：**
```python
def preprocess_image(uploaded_file):
    # 1. 格式檢查
    file_ext = get_file_extension(uploaded_file)
    if file_ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(f"不支援的格式: {file_ext}")
    
    # 2. PDF 轉圖片
    if file_ext == 'pdf':
        images = convert_pdf_to_images(uploaded_file)
    else:
        images = [load_image(uploaded_file)]
    
    # 3. 逐頁處理
    processed_images = []
    for img in images:
        img = rotate_if_needed(img)
        img = denoise(img)
        img = enhance_contrast(img)
        processed_images.append(img)
    
    return processed_images
```

### 4.2 旋轉校正

**檢測方法：**
- 使用文字方向檢測 (Tesseract OSD)
- 若文字大多在 90°/180°/270°，自動旋轉

**實現：**
```python
def rotate_if_needed(image):
    osd = pytesseract.image_to_osd(image)
    rotation = int(re.search('(?<=Rotate: )\d+', osd).group(0))
    
    if rotation != 0:
        image = rotate_image(image, rotation)
        log_preprocessing("rotated", angle=rotation)
    
    return image
```

### 4.3 去噪與增強

**常見問題 & 解決方案：**

| 問題 | 解決方案 | 庫/方法 |
|-----|---------|--------|
| 熱感應紙褪色 | 自適應二值化 | OpenCV adaptiveThreshold |
| 照片反光 | 去除亮斑 | 形態學操作 |
| 低對比度 | 直方圖均衡化 | cv2.equalizeHist |
| 印章/手寫遮擋 | 顏色過濾（保留黑/深色文字） | HSV 色域過濾 |

**示例代碼：**
```python
import cv2
import numpy as np

def enhance_lab_report(image):
    # 轉灰階
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 去噪
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # 自適應二值化（應對不均勻光照）
    binary = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        blockSize=11, C=2
    )
    
    # 去除小噪點
    kernel = np.ones((2,2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return cleaned
```

---

## 五、Stage 2: OCR 識別

### 5.1 技術選型

| 方案 | 優點 | 缺點 | 建議 |
|-----|------|------|------|
| **Azure Form Recognizer** | 表格識別強、API 穩定 | 成本較高、需聯網 | **推薦用於 MVP** |
| **Google Document AI** | 準確度高、支援多語言 | 成本高、數據出境 | 備選方案 |
| **Tesseract 5.x** | 開源免費、可自訓練 | 表格識別弱、需大量優化 | 長期自建方案 |
| **PaddleOCR** | 中文識別好、可本地部署 | 表格結構需額外處理 | 備選 + 自建 |

**MVP 建議：**
- 先用 **Azure Form Recognizer** 快速驗證
- 並行準備 **PaddleOCR + 自訓練模型** 作為長期方案

### 5.2 表格結構檢測

**Azure Form Recognizer 輸出範例：**
```json
{
  "tables": [
    {
      "rows": 5,
      "columns": 4,
      "cells": [
        {
          "rowIndex": 0,
          "columnIndex": 0,
          "text": "檢驗項目",
          "boundingBox": [120, 200, 280, 200, 280, 230, 120, 230]
        },
        {
          "rowIndex": 1,
          "columnIndex": 0,
          "text": "空腹血糖",
          "boundingBox": [120, 230, 280, 230, 280, 260, 120, 260]
        },
        {
          "rowIndex": 1,
          "columnIndex": 1,
          "text": "95",
          "boundingBox": [280, 230, 350, 230, 350, 260, 280, 260]
        },
        // ... 更多 cells
      ]
    }
  ]
}
```

**處理邏輯：**
```python
def extract_table_structure(ocr_result):
    """從 OCR 結果重建表格結構"""
    tables = []
    
    for table in ocr_result['tables']:
        structured_table = {
            'headers': [],
            'rows': []
        }
        
        # 提取表頭
        for cell in table['cells']:
            if cell['rowIndex'] == 0:
                structured_table['headers'].append(cell['text'])
        
        # 按行組織數據
        current_row_idx = 1
        current_row = []
        for cell in sorted(table['cells'], key=lambda x: (x['rowIndex'], x['columnIndex'])):
            if cell['rowIndex'] == 0:
                continue  # 跳過表頭
            
            if cell['rowIndex'] != current_row_idx:
                structured_table['rows'].append(current_row)
                current_row = []
                current_row_idx = cell['rowIndex']
            
            current_row.append({
                'text': cell['text'],
                'confidence': cell.get('confidence', 1.0),
                'bbox': cell['boundingBox']
            })
        
        if current_row:
            structured_table['rows'].append(current_row)
        
        tables.append(structured_table)
    
    return tables
```

---

## 六、Stage 3: 欄位抽取與標準化

### 6.1 項目名稱映射（核心難點）

**挑戰：同一檢驗項目有多種寫法**

**解決方案：多層映射策略**

#### 方案 1: 精確匹配（Exact Match）
```python
EXACT_MATCH_MAP = {
    # 中文
    "空腹血糖": "glucose_fasting",
    "飯前血糖": "glucose_fasting",
    "血糖(空腹)": "glucose_fasting",
    # 英文
    "Fasting Glucose": "glucose_fasting",
    "FBS": "glucose_fasting",
    "AC Sugar": "glucose_fasting",
    # 其他常見項目...
}
```

#### 方案 2: 模糊匹配（Fuzzy Match）
```python
from fuzzywuzzy import fuzz

def fuzzy_match_test_name(input_name, threshold=85):
    """當精確匹配失敗時，使用模糊匹配"""
    best_match = None
    best_score = 0
    
    for known_name, standard_name in EXACT_MATCH_MAP.items():
        score = fuzz.ratio(input_name, known_name)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = standard_name
    
    return best_match, best_score
```

#### 方案 3: 關鍵詞匹配（Keyword Match）
```python
KEYWORD_PATTERNS = {
    "glucose_fasting": ["血糖", "glucose", "sugar"] + ["空腹", "飯前", "fasting", "AC"],
    "cholesterol_total": ["膽固醇", "胆固醇", "cholesterol", "T-CHO"] + ["總", "总", "total"],
    "alt": ["ALT", "GPT", "SGPT", "谷丙", "谷內丙"],
    # ...
}

def keyword_match_test_name(input_name):
    """基於關鍵詞匹配"""
    input_lower = input_name.lower()
    
    for standard_name, keywords_list in KEYWORD_PATTERNS.items():
        # 需要同時包含主關鍵詞 + 修飾詞
        if any(kw in input_lower for kw in keywords_list[:3]) and \
           any(kw in input_lower for kw in keywords_list[3:]):
            return standard_name
    
    return None
```

**綜合策略：**
```python
def map_test_name_to_standard(input_name):
    """三層映射策略"""
    # Layer 1: 精確匹配
    if input_name in EXACT_MATCH_MAP:
        return EXACT_MATCH_MAP[input_name], 1.0, "exact_match"
    
    # Layer 2: 模糊匹配
    fuzzy_result, fuzzy_score = fuzzy_match_test_name(input_name)
    if fuzzy_result and fuzzy_score >= 85:
        return fuzzy_result, fuzzy_score/100, "fuzzy_match"
    
    # Layer 3: 關鍵詞匹配
    keyword_result = keyword_match_test_name(input_name)
    if keyword_result:
        return keyword_result, 0.75, "keyword_match"
    
    # 無法映射
    return None, 0.0, "unmapped"
```

---

### 6.2 數值抽取與類型檢查

**挑戰：**
- OCR 可能把數字識別成字母（如 0→O, 1→l）
- 可能包含特殊符號（如 "<100", ">5.0"）
- 可能有小數點錯誤（如 "9.5" 被識別成 "9,5"）

**解決方案：**
```python
import re

def extract_numeric_value(text):
    """從文字中抽取數值"""
    # 前處理：常見 OCR 錯誤修正
    text = text.replace('O', '0').replace('o', '0')
    text = text.replace('l', '1').replace('I', '1')
    text = text.replace(',', '.')  # 小數點修正
    
    # 處理特殊符號（<, >, ≤, ≥）
    operator = None
    if any(op in text for op in ['<', '>', '≤', '≥', '<=', '>=']):
        operator = re.search(r'[<>≤≥]+', text).group(0)
        text = re.sub(r'[<>≤≥]+', '', text)
    
    # 抽取數字（含小數點）
    match = re.search(r'(\d+\.?\d*)', text)
    if match:
        value = float(match.group(1))
        return {
            'value': value,
            'operator': operator,
            'raw_text': text
        }
    
    return None
```

**類型檢查：**
```python
def validate_numeric_type(value, expected_type):
    """檢查數值類型是否合理"""
    if expected_type == 'integer' and value != int(value):
        return False, "應為整數但有小數"
    
    if expected_type == 'percentage' and not (0 <= value <= 100):
        return False, "百分比應在 0-100 之間"
    
    return True, None
```

---

### 6.3 單位識別與轉換

**單位標準化表（部分）：**

```python
UNIT_CONVERSIONS = {
    # 血糖
    "glucose_fasting": {
        "canonical_unit": "mg/dL",
        "conversions": {
            "mmol/L": lambda x: x * 18.02,
            "mg/dl": lambda x: x,  # 小寫也接受
        }
    },
    # 膽固醇
    "cholesterol_total": {
        "canonical_unit": "mg/dL",
        "conversions": {
            "mmol/L": lambda x: x * 38.67,
            "mg/dl": lambda x: x,
        }
    },
    # 肌酸酐
    "creatinine": {
        "canonical_unit": "mg/dL",
        "conversions": {
            "μmol/L": lambda x: x / 88.4,
            "umol/L": lambda x: x / 88.4,  # 接受 ASCII 版本
            "mg/dl": lambda x: x,
        }
    },
    # ... 其他項目
}

def convert_to_canonical_unit(test_name, value, unit):
    """轉換到標準單位"""
    if test_name not in UNIT_CONVERSIONS:
        return value, unit, False  # 無轉換規則
    
    config = UNIT_CONVERSIONS[test_name]
    canonical = config['canonical_unit']
    
    # 已經是標準單位
    if unit.lower() == canonical.lower():
        return value, canonical, True
    
    # 需要轉換
    if unit in config['conversions']:
        converted_value = config['conversions'][unit](value)
        return converted_value, canonical, True
    
    # 未知單位
    return value, unit, False
```

---

### 6.4 參考範圍解析

**常見格式：**
- `"70-100"` → {low: 70, high: 100}
- `"<200"` → {low: null, high: 200}
- `">40"` → {low: 40, high: null}
- `"70~100"` → {low: 70, high: 100}
- `"陰性"`, `"Negative"` → {type: "qualitative", value: "negative"}

**解析函數：**
```python
def parse_reference_range(text):
    """解析參考範圍"""
    text = text.strip()
    
    # 定性結果（陰性/陽性）
    if any(qual in text.lower() for qual in ['陰性', '阴性', 'negative', '正常', 'normal']):
        return {'type': 'qualitative', 'value': 'negative'}
    
    # 單邊界：< 或 >
    if text.startswith('<') or text.startswith('≤'):
        value = extract_numeric_value(text[1:])
        return {'type': 'upper_bound', 'high': value['value']}
    
    if text.startswith('>') or text.startswith('≥'):
        value = extract_numeric_value(text[1:])
        return {'type': 'lower_bound', 'low': value['value']}
    
    # 範圍：70-100 或 70~100
    range_match = re.match(r'(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)', text)
    if range_match:
        return {
            'type': 'range',
            'low': float(range_match.group(1)),
            'high': float(range_match.group(2))
        }
    
    # 無法解析
    return {'type': 'unparseable', 'raw_text': text}
```

---

## 七、Stage 4: 驗證 (Validation)

### 7.1 合理範圍檢查（生理可能範圍）

**配置表：**
```python
PHYSIOLOGICAL_RANGES = {
    "glucose_fasting": {
        "min": 30,
        "max": 400,
        "unit": "mg/dL",
        "severity": "critical"  # 超出範圍的嚴重程度
    },
    "cholesterol_total": {
        "min": 50,
        "max": 500,
        "unit": "mg/dL",
        "severity": "warning"
    },
    "alt": {
        "min": 0,
        "max": 500,
        "unit": "U/L",
        "severity": "warning"
    },
    # ... 更多項目
}

def check_physiological_range(test_name, value, unit):
    """檢查數值是否在生理可能範圍內"""
    if test_name not in PHYSIOLOGICAL_RANGES:
        return True, None  # 無檢查規則，通過
    
    config = PHYSIOLOGICAL_RANGES[test_name]
    
    # 單位不匹配先轉換
    if unit != config['unit']:
        value, unit, success = convert_to_canonical_unit(test_name, value, unit)
        if not success:
            return False, f"單位無法轉換: {unit}"
    
    # 檢查範圍
    if value < config['min'] or value > config['max']:
        return False, f"數值 {value} 超出生理可能範圍 ({config['min']}-{config['max']} {unit})"
    
    return True, None
```

---

### 7.2 單位-參考範圍一致性檢查

**問題：有時 OCR 會把 value 的單位抓對，但參考範圍的單位抓錯**

```python
def check_unit_consistency(lab_result):
    """檢查數值單位與參考範圍單位是否一致"""
    value_unit = lab_result['unit']
    ref_unit = lab_result['ref_range'].get('unit', value_unit)
    
    if value_unit != ref_unit:
        # 嘗試自動轉換
        test_name = lab_result['test_name']
        if test_name in UNIT_CONVERSIONS:
            # 轉換參考範圍到 value 的單位
            converted_ref = convert_reference_range(
                lab_result['ref_range'], 
                ref_unit, 
                value_unit,
                test_name
            )
            lab_result['ref_range'] = converted_ref
            lab_result['validation_flags'].append("ref_range_unit_converted")
        else:
            # 無法轉換，標記需人工確認
            lab_result['status'] = "needs_review"
            lab_result['validation_flags'].append("unit_mismatch")
    
    return lab_result
```

---

### 7.3 信心分數綜合計算

**多因素信心模型：**

```python
def calculate_overall_confidence(lab_result):
    """綜合計算欄位的信心分數"""
    factors = []
    
    # Factor 1: OCR 識別信心
    ocr_conf = lab_result.get('ocr_confidence', 0.5)
    factors.append(('ocr', ocr_conf, 0.4))  # 權重 40%
    
    # Factor 2: 項目名稱映射信心
    mapping_conf = lab_result.get('mapping_confidence', 0.5)
    factors.append(('mapping', mapping_conf, 0.25))  # 權重 25%
    
    # Factor 3: 數值合理性
    if lab_result.get('value_in_physiological_range', True):
        factors.append(('physiological', 1.0, 0.15))
    else:
        factors.append(('physiological', 0.3, 0.15))
    
    # Factor 4: 單位一致性
    if 'unit_mismatch' not in lab_result.get('validation_flags', []):
        factors.append(('unit', 1.0, 0.1))
    else:
        factors.append(('unit', 0.5, 0.1))
    
    # Factor 5: 參考範圍完整性
    ref_range = lab_result.get('ref_range', {})
    if ref_range.get('type') == 'range' and ref_range.get('low') and ref_range.get('high'):
        factors.append(('ref_complete', 1.0, 0.1))
    else:
        factors.append(('ref_complete', 0.7, 0.1))
    
    # 加權平均
    total_conf = sum(score * weight for name, score, weight in factors)
    
    # 記錄詳細信息供調試
    lab_result['confidence_breakdown'] = {
        name: {'score': score, 'weight': weight} 
        for name, score, weight in factors
    }
    
    return round(total_conf, 3)
```

---

### 7.4 自動標記策略

```python
def apply_validation_flags(lab_result):
    """根據驗證結果自動標記狀態"""
    overall_conf = calculate_overall_confidence(lab_result)
    lab_result['overall_confidence'] = overall_conf
    
    # 決策樹
    if overall_conf < 0.75:
        lab_result['status'] = "needs_review"
        lab_result['review_reason'] = "低信心分數"
    
    elif 'unit_mismatch' in lab_result['validation_flags']:
        lab_result['status'] = "needs_review"
        lab_result['review_reason'] = "單位不一致"
    
    elif not lab_result.get('value_in_physiological_range', True):
        lab_result['status'] = "needs_review"
        lab_result['review_reason'] = "數值超出生理可能範圍"
    
    elif lab_result.get('mapping_method') == 'unmapped':
        lab_result['status'] = "needs_review"
        lab_result['review_reason'] = "無法識別檢驗項目"
    
    else:
        lab_result['status'] = "auto_confirmed"
    
    return lab_result
```

---

## 八、Stage 5: 用戶確認介面

### 8.1 UX 設計原則

**原則 1: 預設信任高信心結果**
- 信心 >= 0.85 且無異常 → 預設勾選"已確認"
- 信心 < 0.75 或有異常 → 高亮顯示，要求確認

**原則 2: 最小化用戶負擔**
- 不要讓用戶重新輸入整份報告
- 只針對需確認的欄位提供快速修改

**原則 3: 視覺化輔助**
- 顯示原始圖像，框選出對應欄位位置
- 用顏色區分狀態（綠=已確認 / 黃=需注意 / 紅=異常）

---

### 8.2 介面 Mockup（文字描述）

```
┌────────────────────────────────────────────────────┐
│  OCR 識別結果                       [查看原圖] 按鈕   │
├────────────────────────────────────────────────────┤
│                                                    │
│  ✓ 已成功識別 12 個檢驗項目                         │
│  ⚠ 2 個項目需要您確認                               │
│                                                    │
├────────────────────────────────────────────────────┤
│  [已確認項目 (10)]  ▼ 展開/收起                     │
│                                                    │
│  ✓ 空腹血糖: 95 mg/dL (參考: 70-100)  [修改]       │
│  ✓ 總膽固醇: 220 mg/dL (參考: <200)   [修改]       │
│  ✓ HDL: 45 mg/dL (參考: >40)          [修改]       │
│  ... (其他 7 項)                                   │
│                                                    │
├────────────────────────────────────────────────────┤
│  [需確認項目 (2)]                                   │
│                                                    │
│  ⚠ 項目 1: ALT (GPT)                               │
│     識別結果: 4? U/L  (數字不清楚)                  │
│     參考範圍: 0-40 U/L                              │
│     信心度: 68%                                     │
│                                                    │
│     [查看原圖位置] 按鈕 (點擊後高亮框選)             │
│                                                    │
│     請確認數值: [___42___] U/L                      │
│     [✓ 確認]  [✗ 刪除此項]                          │
│                                                    │
│  ⚠ 項目 2: 維生素 D                                 │
│     識別結果: 1B ng/mL  (可能是 18?)                │
│     參考範圍: 30-100 ng/mL                          │
│     信心度: 55%                                     │
│                                                    │
│     請確認數值: [___18___] ng/mL                    │
│     [✓ 確認]  [✗ 刪除此項]                          │
│                                                    │
├────────────────────────────────────────────────────┤
│  [無法識別項目]                                     │
│                                                    │
│  ℹ 部分檢驗項目無法自動識別，您可以手動添加          │
│  [+ 手動添加項目] 按鈕                              │
│                                                    │
├────────────────────────────────────────────────────┤
│                [確認全部並繼續] 按鈕                 │
└────────────────────────────────────────────────────┘
```

---

### 8.3 前端數據結構

**API 返回格式：**
```json
{
  "ocr_result_id": "uuid",
  "processing_time_ms": 3245,
  "total_items": 12,
  "auto_confirmed": 10,
  "needs_review": 2,
  "unmapped": 0,
  
  "items": [
    {
      "item_id": "uuid",
      "status": "auto_confirmed",
      "test_name_standard": "glucose_fasting",
      "test_name_display": "空腹血糖",
      "value": 95.0,
      "unit": "mg/dL",
      "ref_range": {
        "type": "range",
        "low": 70,
        "high": 100,
        "unit": "mg/dL"
      },
      "overall_confidence": 0.93,
      "bbox": [120, 230, 350, 260],
      "editable": true
    },
    {
      "item_id": "uuid",
      "status": "needs_review",
      "test_name_standard": "alt",
      "test_name_display": "ALT (GPT)",
      "value": 4,  // OCR 識別成 4，應該是 42
      "value_raw_text": "4?",
      "unit": "U/L",
      "ref_range": {
        "type": "range",
        "low": 0,
        "high": 40,
        "unit": "U/L"
      },
      "overall_confidence": 0.68,
      "review_reason": "低信心分數 + 數值可疑",
      "validation_flags": ["low_ocr_confidence", "suspicious_value"],
      "bbox": [120, 260, 350, 290],
      "editable": true
    }
    // ... 其他項目
  ],
  
  "original_image_url": "https://storage.../lab_report_uuid.jpg"
}
```

---

## 九、Stage 6: 結構化儲存

### 9.1 數據庫 Schema

**lab_results 表（PostgreSQL）：**
```sql
CREATE TABLE lab_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    -- 標準化欄位
    test_name VARCHAR(100) NOT NULL,  -- 標準化名稱 (glucose_fasting)
    test_name_display VARCHAR(200),   -- 顯示名稱 (空腹血糖)
    test_name_raw TEXT,               -- OCR 原始文字
    
    value NUMERIC(10,3),
    value_operator VARCHAR(5),        -- <, >, ≤, ≥
    value_raw_text TEXT,              -- OCR 原始文字
    
    unit VARCHAR(20),
    unit_raw_text TEXT,
    
    -- 參考範圍
    ref_range_type VARCHAR(20),       -- range / upper_bound / lower_bound / qualitative
    ref_range_low NUMERIC(10,3),
    ref_range_high NUMERIC(10,3),
    ref_range_unit VARCHAR(20),
    ref_range_raw_text TEXT,
    
    -- 元數據
    test_date DATE,
    lab_name VARCHAR(200),
    
    -- OCR 與驗證
    ocr_confidence NUMERIC(3,2),
    overall_confidence NUMERIC(3,2),
    mapping_method VARCHAR(50),       -- exact_match / fuzzy_match / keyword_match
    mapping_confidence NUMERIC(3,2),
    
    status VARCHAR(20) NOT NULL,      -- auto_confirmed / needs_review / user_confirmed / rejected
    validation_flags JSONB,
    review_reason TEXT,
    
    -- 圖像位置
    bbox JSONB,                       -- [x1, y1, x2, y2]
    source_image_id UUID REFERENCES uploaded_images(image_id),
    
    -- 版本與追溯
    ocr_processing_version VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    confirmed_by UUID REFERENCES users(user_id),
    
    -- 索引
    INDEX idx_user_test (user_id, test_name),
    INDEX idx_status (status),
    INDEX idx_test_date (test_date)
);
```

**uploaded_images 表：**
```sql
CREATE TABLE uploaded_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    file_path TEXT NOT NULL,
    file_size_bytes INT,
    mime_type VARCHAR(50),
    
    -- OCR 元數據
    ocr_result_id UUID,
    ocr_status VARCHAR(20),           -- pending / processing / completed / failed
    ocr_processing_version VARCHAR(20),
    processed_at TIMESTAMP,
    
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,             -- 軟刪除
    
    INDEX idx_user_upload (user_id, uploaded_at)
);
```

---

### 9.2 儲存與檢索 API 設計

**POST /api/ocr/upload**
```json
// Request
{
  "user_id": "uuid",
  "file": "multipart/form-data"
}

// Response
{
  "image_id": "uuid",
  "status": "processing",
  "estimated_completion_sec": 10
}
```

**GET /api/ocr/result/{image_id}**
```json
// Response (同 8.3 節的數據結構)
{
  "ocr_result_id": "uuid",
  "items": [...],
  "status": "completed"
}
```

**POST /api/ocr/confirm**
```json
// Request
{
  "ocr_result_id": "uuid",
  "confirmed_items": [
    {
      "item_id": "uuid",
      "value": 42,  // 用戶修正後的值
      "status": "user_confirmed"
    }
  ],
  "rejected_items": ["uuid", "uuid"]
}

// Response
{
  "success": true,
  "saved_count": 10,
  "rejected_count": 2
}
```

---

## 十、錯誤處理與邊界情況

### 10.1 常見錯誤場景

| 場景 | 系統行為 | 用戶體驗 |
|-----|---------|---------|
| **上傳的不是檢驗報告** | 圖像分析未檢測到表格結構 | 提示"未檢測到檢驗報告，請確認圖片" |
| **圖片過於模糊** | OCR 信心普遍 < 0.6 | 提示"圖片不清晰，建議重新拍攝" |
| **多頁 PDF** | 逐頁處理，最多支援 5 頁 | 顯示"已處理 5 頁，共識別 XX 項" |
| **無法識別任何項目** | unmapped 比例 > 80% | 提示"自動識別失敗，建議手動輸入" + 提供手動輸入表單 |
| **完全無法解析的格式** | OCR API 返回錯誤 | 提示"無法識別此格式，請聯繫客服" |

---

### 10.2 降級方案

**當 OCR 完全失敗時，提供手動輸入：**

```
┌────────────────────────────────────────┐
│  自動識別失敗                           │
│                                        │
│  我們無法自動讀取您的檢驗報告，         │
│  您可以手動輸入關鍵數據：               │
│                                        │
│  [選擇檢驗項目] 下拉選單                │
│    - 空腹血糖                          │
│    - 總膽固醇                          │
│    - ALT                               │
│    - ... (20 個常用項目)               │
│                                        │
│  數值: [____] [單位下拉: mg/dL]        │
│  檢驗日期: [日期選擇器]                 │
│                                        │
│  [+ 添加更多項目]  [保存]              │
└────────────────────────────────────────┘
```

---

## 十一、OCR 失敗與人工流程 SLA

### 11.1 觸發條件

以下任一條件觸發人工流程：
- OCR 結果 `needs_review` 比例 > 30%
- 核心指標（Top 10）抽取數量 < 6
- 單頁 OCR 置信度均值 < 0.70
- 關鍵欄位（血糖、血脂、ALT/AST、肌酸酐）無法識別

### 11.2 人工處理流程

```
OCR 失敗 → 自動工單 → 營養師/審核人員確認 → 回寫結構化數據 → 通知用戶完成
```

### 11.3 SLA 建議

| 場景 | 處理時限 | 用戶提示 |
|-----|---------|---------|
| 標準 OCR 失敗 | 24 小時內完成人工確認 | "資料需人工確認，預計24小時內完成" |
| 緊急標記（用戶主動提交） | 12 小時內 | "已加急處理" |
| 連續失敗（同用戶 2 次以上） | 72 小時內完成並建議改上傳方式 | "建議改用掃描或更清晰照片" |

### 11.4 失敗原因記錄（用於優化）

每次 OCR 失敗需記錄：
- 失敗原因（模糊/遮擋/格式異常/非檢驗報告）
- 處理方式（人工修正/要求重傳/手動輸入）
- 處理耗時
- 關聯報告格式（醫院/健檢中心）

---

## 十二、性能與成本優化

### 12.1 性能指標目標

| 指標 | 目標值 | 測量方法 |
|-----|-------|---------|
| 單張圖片處理時間 | < 10 秒 | 從上傳到返回結果 |
| OCR API 調用成功率 | > 98% | 監控 API 錯誤率 |
| 用戶確認耗時 | < 60 秒 | 前端埋點統計 |
| 欄位抽取準確率 | > 95% (經用戶確認後) | 人工抽樣驗證 |

---

### 12.2 成本優化策略

**如果使用 Azure Form Recognizer：**
- 成本約 **$0.01 - 0.05 / 頁**
- 月處理 1000 份報告 ≈ $10 - $50

**優化方案：**
1. **快取與去重**：同一用戶重複上傳同一報告時，直接返回快取結果
2. **批次處理**：累積多張圖片一起調用 API（如果 API 支援）
3. **圖像預處理**：減少 API 調用失敗率，避免重複處理
4. **長期自建**：當月處理量 > 5000 份時，考慮自建 OCR 模型

---

## 十三、測試與驗收

### 13.1 測試數據集準備

**收集 50-100 份真實健檢報告，涵蓋：**
- 不同醫院/健檢中心（至少 5 家）
- 不同格式（彩色/黑白、清晰/模糊）
- 不同拍攝條件（照片/掃描、橫拍/豎拍）
- 邊界情況（手寫備註、印章遮擋、折痕）

**標注 Ground Truth：**
- 對每份報告手動標註正確值
- 記錄哪些欄位是"難識別"的（用於評估系統表現）

---

### 13.2 驗收標準

| 測試類別 | 通過標準 |
|---------|---------|
| **抽取完整度** | 核心 15 項指標，90% 以上能被抽取（無論信心高低） |
| **自動確認準確率** | 狀態為 auto_confirmed 的項目，準確率 > 98% |
| **需確認標記準確性** | 真正有問題的項目，95% 以上被標記為 needs_review |
| **無誤判率** | 正確的值不應被標記為需確認（誤判率 < 5%） |
| **用戶修正率** | 經用戶確認後，最終準確率 > 95% |
| **處理時間** | 95% 的圖片在 10 秒內完成處理 |

---

### 13.3 測試案例清單（部分示例）

| 測試案例 ID | 描述 | 預期結果 |
|-----------|------|---------|
| TC-OCR-001 | 清晰標準格式報告 | 所有欄位自動確認，信心 > 0.9 |
| TC-OCR-002 | 模糊照片 | 大部分欄位標記需確認 |
| TC-OCR-003 | 有手寫備註的報告 | 印刷欄位正常識別，手寫部分忽略 |
| TC-OCR-004 | 參考範圍缺失 | 能識別數值，參考範圍標記為空 |
| TC-OCR-005 | 單位不一致（mmol/L vs mg/dL） | 自動轉換或標記需確認 |
| TC-OCR-006 | 項目名稱非標準寫法 | 能通過模糊匹配映射到標準欄位 |
| TC-OCR-007 | 數值超出生理範圍 | 標記為異常，要求確認 |
| TC-OCR-008 | OCR 識別錯誤（0 → O） | 數值校驗失敗，標記需確認 |

---

## 十四、後續優化方向

### 13.1 短期優化（3-6 個月）

1. **累積訓練數據**：收集用戶修正後的數據，用於優化映射規則
2. **A/B 測試**：不同預處理參數對識別率的影響
3. **多版本檢驗報告模板識別**：針對常見醫院建立專用模板
4. **用戶反饋閉環**：用戶可標記"識別錯誤"，自動進入優化隊列

### 13.2 長期優化（6-12 個月）

1. **自建 OCR 模型**：
   - 基於 PaddleOCR 微調
   - 針對台灣健檢報告特化訓練
   - 成本降低 80%+

2. **智能表格理解**：
   - 不依賴固定表格結構
   - 能處理自由格式的檢驗報告

3. **多模態融合**：
   - 結合歷史數據推測當前識別是否合理
   - 例如：某用戶上次空腹血糖 95，這次識別成 950 → 可能是 95.0

---

## 十五、RD 開發清單（可直接開票）

### Sprint 1: 基礎 Pipeline (2 周)
- [ ] 圖像上傳 API 與儲存
- [ ] 集成 Azure Form Recognizer API
- [ ] 圖像預處理（旋轉、去噪、增強）
- [ ] 表格結構解析
- [ ] 基礎數據庫 schema 建立

### Sprint 2: 欄位抽取與映射 (2 周)
- [ ] 項目名稱映射表（15 個核心項目）
- [ ] 精確匹配 + 模糊匹配引擎
- [ ] 數值抽取與 OCR 錯誤修正
- [ ] 單位識別與轉換
- [ ] 參考範圍解析

### Sprint 3: 驗證與信心計算 (1.5 周)
- [ ] 生理範圍檢查
- [ ] 單位一致性檢查
- [ ] 綜合信心分數計算
- [ ] 自動標記邏輯（auto_confirmed / needs_review）

### Sprint 4: 用戶確認介面 (1.5 周)
- [ ] OCR 結果展示頁面
- [ ] 原圖查看與 bbox 標註
- [ ] 需確認項目編輯功能
- [ ] 確認提交與資料儲存

### Sprint 5: 測試與優化 (1 周)
- [ ] 準備 50 份測試報告
- [ ] 標註 Ground Truth
- [ ] 執行驗收測試
- [ ] 性能優化（處理時間 < 10 秒）

---

## 十六、常見問題 FAQ

**Q1: OCR 能 100% 準確嗎？**
A: 不能。所以我們設計了信心分數與人工確認機制，確保低信心數據不會被直接使用。

**Q2: 如果用戶上傳的不是檢驗報告怎麼辦？**
A: 系統會檢測表格結構，如果未檢測到或識別項目過少，會提示用戶重新上傳或手動輸入。

**Q3: 是否支援多頁 PDF？**
A: 支援，但 MVP 階段限制最多 5 頁，避免處理時間過長。

**Q4: 如何處理手寫備註？**
A: 目前忽略手寫部分，只識別印刷文字。未來可考慮手寫識別模組。

**Q5: 成本多高？**
A: 使用 Azure Form Recognizer 約 $0.01-0.05/頁，自建模型可降低 80% 成本。

**Q6: 用戶隱私如何保護？**
A: 圖像僅用於 OCR 處理，處理完成後可選擇刪除。所有資料加密儲存，符合 GDPR/個資法。

---

**文檔版本**: v1.0  
**最後更新**: 2026-01-16  
**維護者**: 技術團隊  
**審核者**: 產品 + 營養師團隊
