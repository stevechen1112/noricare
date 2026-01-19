"""
完整流程測試腳本
直接測試 API 端點，跳過 Flutter UI
"""
import requests
import json
import time
from pathlib import Path
import sys
import io

# 修復 Windows 終端編碼問題
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"
DATA_DIR = Path(r"C:\Users\User\Desktop\personalhealth\steve_personaldata")

def test_full_flow():
    print("=" * 80)
    print("開始完整流程測試")
    print("=" * 80)
    
    # Step 1: 創建使用者
    print("\n[Step 1] 創建使用者資料")
    user_data = {
        "name": "Steve",
        "age": 46,
        "gender": "male",
        "height_cm": 178.8,
        "weight_kg": 78.8,
        "health_goals": ["控制血糖", "減重", "提升精力"],
        "lifestyle": {
            "activity_level": "sedentary",
            "dietary_preference": "無特殊偏好",
            "eating_habits": ["外食族"],
            "allergies": []
        }
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    if response.status_code != 200:
        print(f"[ERROR] 創建使用者失敗: {response.status_code}")
        print(response.text)
        return
    
    user_profile = response.json()
    print(f"[OK] 使用者已創建: {user_profile['name']} (ID: {user_profile['id']})")
    print(f"   BMI: {user_profile['bmi']:.2f}")
    
    # Step 2: 上傳所有健康報告圖片
    print(f"\n[Step 2] 上傳健康報告圖片")
    image_files = sorted(DATA_DIR.glob("*.jpg"))
    print(f"   找到 {len(image_files)} 張圖片")
    
    file_ids = []
    for img_file in image_files:
        print(f"\n   上傳: {img_file.name}")
        with open(img_file, "rb") as f:
            files = {"file": (img_file.name, f, "image/jpeg")}
            response = requests.post(f"{BASE_URL}/ocr/upload", files=files)
        
        if response.status_code != 200:
            print(f"   [ERROR] 上傳失敗: {response.status_code}")
            continue
        
        result = response.json()
        file_id = result["file_id"]
        file_ids.append(file_id)
        print(f"   [OK] 上傳成功: {file_id}")
        
        # 等待 OCR 處理
        print(f"   [WAIT] 等待 OCR 處理...")
        for attempt in range(30):  # 最多等待 30 秒
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/ocr/result/{file_id}")
            if response.status_code == 200:
                ocr_result = response.json()
                if ocr_result["status"] == "completed":
                    fields = ocr_result["data"]["fields"]
                    print(f"   [OK] OCR 完成: 識別出 {len(fields)} 個指標")
                    for key, value in fields.items():
                        print(f"      - {key}: {value.get('value')} {value.get('unit', '')}")
                    break
        else:
            print(f"   [WARN] OCR 處理超時")
    
    # Step 3: 合併所有健康數據
    print(f"\n[Step 3] 合併健康數據")
    all_health_data = {}
    abnormal_items = []
    
    # 參考範圍（從 Flutter 移植）
    reference_ranges = {
        "Glucose": {"min": 70, "max": 99, "unit": "mg/dL"},
        "HbA1c": {"min": 4.0, "max": 5.6, "unit": "%"},
        "Creatinine": {"min": 0.7, "max": 1.3, "unit": "mg/dL"},
        "eGFR": {"min": 90, "max": 999, "unit": "mL/min/1.73m²"},
        "飯後血糖 (Glucose PC)": {"min": 70, "max": 140, "unit": "mg/dL"},
        "醣化血色素 (HbA1c)": {"min": 4.0, "max": 5.6, "unit": "%"},
    }
    
    for file_id in file_ids:
        response = requests.get(f"{BASE_URL}/ocr/result/{file_id}")
        if response.status_code == 200:
            ocr_result = response.json()
            if ocr_result["status"] == "completed":
                fields = ocr_result["data"]["fields"]
                for key, value_data in fields.items():
                    val = value_data.get("value")
                    unit = value_data.get("unit", "")
                    ref_range = value_data.get("reference_range", "")
                    
                    # 判斷狀態
                    status = "Normal"
                    if key in reference_ranges:
                        ref = reference_ranges[key]
                        if val and (val < ref["min"] or val > ref["max"]):
                            status = "High" if val > ref["max"] else "Low"
                            abnormal_items.append(f"{key}: {val} {unit} ({'偏高' if status == 'High' else '偏低'})")
                    
                    all_health_data[key] = {
                        "value": val,
                        "unit": unit,
                        "reference_range": ref_range,
                        "status": status
                    }
    
    print(f"   [OK] 總共合併 {len(all_health_data)} 個健康指標")
    print(f"   [WARN] 異常指標 ({len(abnormal_items)} 項):")
    for item in abnormal_items:
        print(f"      - {item}")
    
    # Step 4: 生成 AI 報告
    print(f"\n[Step 4] 生成 AI 健康報告")
    recommendation_request = {
        "user_profile": user_profile,
        "health_data": all_health_data,
        "abnormal_items": abnormal_items
    }
    
    print("   [API] 發送請求到 /recommendation/generate...")
    print(f"   - 使用者: {user_profile['name']}")
    print(f"   - 健康指標: {len(all_health_data)} 項")
    print(f"   - 異常項目: {len(abnormal_items)} 項")
    
    try:
        response = requests.post(
            f"{BASE_URL}/recommendation/generate",
            json=recommendation_request,
            timeout=120  # 2 分鐘超時
        )
        
        if response.status_code != 200:
            print(f"\n[ERROR] AI 報告生成失敗: {response.status_code}")
            print("錯誤詳情:")
            print(response.text)
            return
        
        report = response.json()
        print(f"\n[SUCCESS] AI 報告生成成功!")
        print("=" * 80)
        print(f"健康評分: {report['health_score']} / 100")
        print("=" * 80)
        
        # 顯示報告內容
        print(f"\n[飲食建議] ({len(report['food_advice'])} 則)")
        for advice in report['food_advice']:
            print(f"\n【{advice['title']}】")
            content = advice['content'][:500]  # 只顯示前 500 字
            print(content)
            if len(advice['content']) > 500:
                print(f"... (共 {len(advice['content'])} 字)")
        
        print(f"\n[保健建議] ({len(report['supplement_advice'])} 則)")
        for advice in report['supplement_advice']:
            print(f"\n【{advice['title']}】")
            content = advice['content'][:500]
            print(content)
            if len(advice['content']) > 500:
                print(f"... (共 {len(advice['content'])} 字)")
        
        print(f"\n[餐飲計劃]")
        meal_plan = report['meal_plan'].get('markdown_content', '')[:500]
        print(meal_plan)
        if len(report['meal_plan'].get('markdown_content', '')) > 500:
            print(f"... (共 {len(report['meal_plan'].get('markdown_content', ''))} 字)")
        
        print("\n" + "=" * 80)
        print("[SUCCESS] 完整流程測試成功！")
        print("=" * 80)
        
        # 保存完整報告到檔案
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("\n[FILE] 完整報告已保存至: test_report.json")
        
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] 請求超時 (120秒)")
    except Exception as e:
        print(f"\n[ERROR] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_flow()
