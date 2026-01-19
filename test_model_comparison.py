"""
Gemini Pro vs Flash 性能對比測試
測試項目：OCR 速度、報告生成速度、準確度
"""
import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# 測試圖片路徑
TEST_IMAGES = [
    r"C:\Users\User\Desktop\personalhealth\steve_personaldata\40108.jpg",
    r"C:\Users\User\Desktop\personalhealth\steve_personaldata\40109.jpg",
]

# 測試數據
TEST_HEALTH_DATA = {
    "Glucose": {"value": 117.0, "unit": "mg/dL"},
    "Creatinine": {"value": 1.05, "unit": "mg/dL"},
    "HbA1c": {"value": 5.8, "unit": "%"},
}

def test_ocr_speed(model_name: str, image_path: str):
    """測試 OCR 速度"""
    print(f"\n[{model_name}] 測試 OCR: {Path(image_path).name}")
    
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name=model_name)
    
    from PIL import Image
    img = Image.open(image_path)
    
    prompt = """
    請從這張健檢報告中提取檢驗數據，以 JSON 格式輸出：
    {"fields": {"指標名稱": {"value": 數值, "unit": "單位"}}}
    """
    
    start = time.time()
    try:
        response = model.generate_content([prompt, img])
        elapsed = time.time() - start
        
        # 提取 JSON
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(text)
        field_count = len(result.get("fields", {}))
        
        return {
            "success": True,
            "time": round(elapsed, 2),
            "field_count": field_count,
            "response_length": len(response.text)
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "time": round(elapsed, 2),
            "error": str(e)
        }

def test_report_generation(model_name: str):
    """測試報告生成速度與品質"""
    print(f"\n[{model_name}] 測試報告生成")
    
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name=model_name)
    
    prompt = f"""
你是台灣專業營養師。根據以下健檢數據，生成一份簡短的營養建議（約 500 字）：

健檢數據：
- 血糖 (Glucose): 117 mg/dL（空腹標準 <100）
- 肌酸酐 (Creatinine): 1.05 mg/dL
- 糖化血色素 (HbA1c): 5.8%（正常 <5.7）

使用者：46 歲男性，BMI 24.6（過重），目標：控制血糖、減重

請提供：
1. 飲食建議（3點）
2. 補充品建議（2種）
3. 注意事項（2點）

請用繁體中文，專業但易懂。
"""
    
    start = time.time()
    try:
        response = model.generate_content(prompt)
        elapsed = time.time() - start
        
        text = response.text
        word_count = len(text)
        
        # 簡單品質評估
        quality_score = 0
        if "飲食" in text: quality_score += 1
        if "補充品" in text or "保健" in text: quality_score += 1
        if "血糖" in text: quality_score += 1
        if "建議" in text: quality_score += 1
        if word_count >= 300: quality_score += 1
        
        return {
            "success": True,
            "time": round(elapsed, 2),
            "word_count": word_count,
            "quality_score": quality_score,
            "preview": text[:200] + "..."
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "time": round(elapsed, 2),
            "error": str(e)
        }

def run_comparison():
    """執行完整對比測試"""
    models = [
        "gemini-3-flash-preview",
        "gemini-3-pro-preview"
    ]
    
    results = {
        "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": {}
    }
    
    print("=" * 60)
    print("Gemini Pro vs Flash 性能對比測試")
    print("=" * 60)
    
    for model_name in models:
        print(f"\n\n{'=' * 60}")
        print(f"測試模型: {model_name}")
        print(f"{'=' * 60}")
        
        model_results = {
            "ocr_tests": [],
            "report_generation": None
        }
        
        # 測試 OCR（每張圖片測一次）
        for img_path in TEST_IMAGES:
            if os.path.exists(img_path):
                ocr_result = test_ocr_speed(model_name, img_path)
                model_results["ocr_tests"].append({
                    "image": Path(img_path).name,
                    **ocr_result
                })
                print(f"  ✓ OCR 耗時: {ocr_result['time']}s")
            else:
                print(f"  ⚠️ 圖片不存在: {img_path}")
        
        # 測試報告生成
        report_result = test_report_generation(model_name)
        model_results["report_generation"] = report_result
        if report_result["success"]:
            print(f"  ✓ 報告生成耗時: {report_result['time']}s")
            print(f"  ✓ 字數: {report_result['word_count']}")
            print(f"  ✓ 品質評分: {report_result['quality_score']}/5")
        
        results["models"][model_name] = model_results
    
    # 生成對比報告
    print("\n\n" + "=" * 60)
    print("對比結果總結")
    print("=" * 60)
    
    for model_name, data in results["models"].items():
        print(f"\n{model_name}:")
        
        # OCR 平均時間
        ocr_times = [t["time"] for t in data["ocr_tests"] if t["success"]]
        if ocr_times:
            avg_ocr = sum(ocr_times) / len(ocr_times)
            print(f"  OCR 平均耗時: {avg_ocr:.2f}s")
        
        # 報告生成
        if data["report_generation"] and data["report_generation"]["success"]:
            rg = data["report_generation"]
            print(f"  報告生成耗時: {rg['time']}s")
            print(f"  報告品質: {rg['quality_score']}/5")
    
    # 儲存完整結果
    output_file = "model_comparison_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n完整結果已儲存至: {output_file}")
    
    return results

if __name__ == "__main__":
    try:
        results = run_comparison()
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試失敗: {e}")
        import traceback
        traceback.print_exc()
