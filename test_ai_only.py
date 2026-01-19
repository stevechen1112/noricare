"""
簡化測試：直接測試 AI 報告生成
跳過 OCR 步驟，使用已知的健康數據
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 模擬已經處理好的健康數據（來自你的圖片）
test_data = {
    "user_profile": {
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
        },
        "id": "test-user-id",
        "bmi": 24.65
    },
    "health_data": {
        "Glucose": {
            "value": 169,
            "unit": "mg/dL",
            "reference_range": "< 140 (飯後)",
            "status": "High"
        },
        "HbA1c": {
            "value": 5.8,
            "unit": "%",
            "reference_range": "< 5.7",
            "status": "High"
        },
        "Creatinine": {
            "value": 1.05,
            "unit": "mg/dL",
            "reference_range": "0.7-1.3",
            "status": "Normal"
        },
        "eGFR": {
            "value": 76.38,
            "unit": "mL/min/1.73m²",
            "reference_range": "> 90",
            "status": "Low"
        }
    },
    "abnormal_items": [
        "Glucose: 169 mg/dL (偏高)",
        "HbA1c: 5.8 % (偏高)",
        "eGFR: 76.38 mL/min/1.73m² (偏低)"
    ]
}

print("=" * 80)
print("直接測試 AI 報告生成")
print("=" * 80)
print(f"\n使用者: {test_data['user_profile']['name']}")
print(f"健康指標: {len(test_data['health_data'])} 項")
print(f"異常項目: {len(test_data['abnormal_items'])} 項")
print("\n發送請求到 /recommendation/generate...")

try:
    response = requests.post(
        f"{BASE_URL}/recommendation/generate",
        json=test_data,
        timeout=120
    )
    
    if response.status_code != 200:
        print(f"\n[ERROR] 狀態碼: {response.status_code}")
        print("錯誤詳情:")
        print(response.text)
    else:
        report = response.json()
        print(f"\n[SUCCESS] AI 報告生成成功!")
        print("=" * 80)
        print(f"健康評分: {report['health_score']} / 100")
        print("=" * 80)
        
        print(f"\n[飲食建議] {len(report['food_advice'])} 則")
        if report['food_advice']:
            print(f"標題: {report['food_advice'][0]['title']}")
            print(f"內容長度: {len(report['food_advice'][0]['content'])} 字")
        
        print(f"\n[保健建議] {len(report['supplement_advice'])} 則")
        if report['supplement_advice']:
            print(f"標題: {report['supplement_advice'][0]['title']}")
            print(f"內容長度: {len(report['supplement_advice'][0]['content'])} 字")
        
        print(f"\n[餐飲計劃]")
        print(f"內容長度: {len(report['meal_plan'].get('markdown_content', ''))} 字")
        
        # 保存報告
        with open("test_ai_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("\n報告已保存至: test_ai_report.json")
        
except requests.exceptions.Timeout:
    print("\n[TIMEOUT] 請求超時 (120秒)")
except Exception as e:
    print(f"\n[ERROR] 發生錯誤: {e}")
    import traceback
    traceback.print_exc()
