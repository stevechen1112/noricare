"""
完整版 MVP - 包含食物攝取 + 保健食品建議
"""
import asyncio
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-3-pro-preview")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=GEMINI_MODEL)

DATA_DIR = r"C:\Users\User\Desktop\personalhealth\steve_personaldata"

# ============ 使用者資料 ============
USER_PROFILE = {
    "age": 40,
    "gender": "male",
    "height_cm": 178.8,
    "weight_kg": 78.8,
    "goal": "控制血糖、維持腎功能、整體健康管理",
    "allergies": [],  # 過敏原
    "current_medications": [],  # 目前用藥
    "dietary_restrictions": []  # 飲食限制
}

# ============ 從之前分析得到的完整健檢數據 ============
HEALTH_DATA = {
    "GLUCOSE": {"value": 117.0, "unit": "mg/dL", "reference_range": "70-99", "status": "偏高"},
    "HbA1c": {"value": 5.8, "unit": "%", "reference_range": "4.0-5.6", "status": "偏高"},
    "Glucose_PC": {"value": 169, "unit": "mg/dL", "reference_range": "<140", "status": "偏高"},
    "Creatinine": {"value": 1.05, "unit": "mg/dL", "reference_range": "0.7-1.2", "status": "正常"},
    "eGFR": {"value": 92, "unit": "mL/min/1.73m²", "reference_range": ">60", "status": "正常"},
    "BUN": {"value": 16, "unit": "mg/dL", "reference_range": "7-20", "status": "正常"},
    "AST/GOT": {"value": 38, "unit": "U/L", "reference_range": "<40", "status": "正常"},
    "ALT/GPT": {"value": 32, "unit": "U/L", "reference_range": "<40", "status": "正常"},
    "Systolic_BP": {"value": 119, "unit": "mmHg", "reference_range": "<120", "status": "正常"},
    "Diastolic_BP": {"value": 71, "unit": "mmHg", "reference_range": "<80", "status": "正常"},
    "BMI": {"value": 24.6, "unit": "kg/m²", "reference_range": "18.5-24", "status": "過重"},
    "Hb": {"value": 14.3, "unit": "g/dL", "reference_range": "13.5-17.5", "status": "正常"},
    "Na": {"value": 138, "unit": "mEq/L", "reference_range": "135-145", "status": "正常"},
    "K": {"value": 4.3, "unit": "mEq/L", "reference_range": "3.5-5.1", "status": "正常"},
    "Calcium": {"value": 8.9, "unit": "mg/dL", "reference_range": "8.6-10.2", "status": "正常"},
}

# ============ 異常項目摘要 ============
ABNORMAL_ITEMS = [
    "空腹血糖 117 mg/dL (偏高，糖尿病前期)",
    "HbA1c 5.8% (偏高，糖尿病前期)",
    "飯後血糖 169 mg/dL (顯著偏高)",
    "BMI 24.6 (過重，需減重約 4-5 公斤)"
]

async def generate_food_recommendations() -> str:
    """生成食物攝取建議"""
    
    prompt = f"""
    你是一位專業的台灣營養師。請根據以下健康數據，提供**具體的食物攝取建議**。

    【使用者資料】
    - 年齡: {USER_PROFILE['age']} 歲，性別: 男性
    - 身高: {USER_PROFILE['height_cm']} cm，體重: {USER_PROFILE['weight_kg']} kg
    - BMI: 24.6 (過重)
    - 健康目標: {USER_PROFILE['goal']}

    【異常指標】
    {json.dumps(ABNORMAL_ITEMS, ensure_ascii=False, indent=2)}

    【完整健檢數據】
    {json.dumps(HEALTH_DATA, ensure_ascii=False, indent=2)}

    請提供：

    ## 🥗 每日食物攝取建議

    ### 1. 主食類（澱粉）
    - 建議每日攝取量
    - 推薦食材（標註 GI 值）
    - 具體份量換算

    ### 2. 蛋白質類
    - 建議每日攝取量（克）
    - 推薦食材排序（豆 > 魚 > 蛋 > 肉）
    - 每餐建議份量

    ### 3. 蔬菜類
    - 建議每日攝取量
    - 特別推薦的穩糖蔬菜
    - 烹調建議

    ### 4. 水果類
    - 建議每日攝取量（限制）
    - 低 GI 水果清單
    - 應避免的高糖水果

    ### 5. 油脂類
    - 建議用油種類
    - 每日攝取量

    ### 6. 飲品
    - 每日水分攝取量
    - 推薦飲品
    - 禁止飲品

    請用台灣常見食材，標註具體克數或份量。
    """
    
    response = model.generate_content(prompt)
    return response.text

async def generate_supplement_recommendations() -> str:
    """生成保健食品建議（含安全守門）"""
    
    prompt = f"""
    你是一位專業的台灣營養師，同時具備保健食品諮詢專業。請根據以下健康數據，提供**保健食品建議**。

    【重要安全資訊】
    - 腎功能: eGFR 92 (正常，無需限制蛋白質補充)
    - 肝功能: AST 38, ALT 32 (正常)
    - 目前無服用藥物

    【主要健康問題】
    1. 糖尿病前期（空腹血糖 117, HbA1c 5.8%, 飯後血糖 169）
    2. 體重過重（BMI 24.6）

    【完整健檢數據】
    {json.dumps(HEALTH_DATA, ensure_ascii=False, indent=2)}

    請提供保健食品建議，格式如下：

    ## 💊 保健食品建議

    ### 🔴 優先建議（針對主要問題）

    對於每個建議的保健食品，請提供：
    1. **品名**
    2. **建議劑量**（每日）
    3. **作用機轉**（為什麼對這個問題有幫助）
    4. **台灣市售品牌參考**（2-3個）
    5. **服用時機**（飯前/飯後/睡前）
    6. **注意事項**

    ### 🟡 輔助建議（整體健康）

    ### 🟢 可考慮（非必要但有益）

    ### ⚠️ 安全守門提醒
    - 不建議的保健食品（與此健康狀況可能有衝突）
    - 需要諮詢醫師才能使用的項目
    - 劑量上限警告

    ### 📋 每日服用時間表
    提供一個簡單的時間表，方便遵循。

    請確保建議符合台灣法規，不做醫療宣稱。
    """
    
    response = model.generate_content(prompt)
    return response.text

async def generate_weekly_meal_plan() -> str:
    """生成一週完整菜單"""
    
    prompt = f"""
    你是一位專業的台灣營養師。請為一位 40 歲男性（糖尿病前期、BMI 24.6）設計一週的完整菜單。

    【目標】
    1. 控制血糖（空腹 <100, 飯後 <140）
    2. 減重（目標減 4-5 公斤）
    3. 維持腎功能

    【每日營養目標】
    - 熱量: 約 1800-2000 大卡
    - 碳水化合物: 佔總熱量 40-45%（優先選低 GI）
    - 蛋白質: 佔總熱量 20-25%（約 90-100g）
    - 脂肪: 佔總熱量 30-35%（優先不飽和脂肪）
    - 膳食纖維: 25-30g

    請提供完整 7 天菜單，每天包含：
    - 早餐（含熱量估算）
    - 午餐（含熱量估算）
    - 晚餐（含熱量估算）
    - 點心（如果需要）

    格式範例：
    ## 週一
    ### 早餐 (約 400 kcal)
    - 食物 1（份量）
    - 食物 2（份量）

    請使用台灣常見食材，考慮外食族的便利性。
    """
    
    response = model.generate_content(prompt)
    return response.text

async def main():
    print("=" * 70)
    print("🏥 Personal Health MVP - 完整營養建議系統")
    print("=" * 70)
    
    # 1. 食物攝取建議
    print("\n📋 【Part 1】生成食物攝取建議...")
    food_advice = await generate_food_recommendations()
    
    # 2. 保健食品建議
    print("💊 【Part 2】生成保健食品建議...")
    supplement_advice = await generate_supplement_recommendations()
    
    # 3. 一週菜單
    print("🍽️ 【Part 3】生成一週菜單...")
    meal_plan = await generate_weekly_meal_plan()
    
    # 輸出完整報告
    print("\n" + "=" * 70)
    print("📊 完整營養建議報告")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("🥗 PART 1: 每日食物攝取建議")
    print("=" * 70)
    print(food_advice)
    
    print("\n" + "=" * 70)
    print("💊 PART 2: 保健食品建議")
    print("=" * 70)
    print(supplement_advice)
    
    print("\n" + "=" * 70)
    print("🍽️ PART 3: 一週菜單計畫")
    print("=" * 70)
    print(meal_plan)
    
    print("\n" + "=" * 70)
    print("✅ 完整建議生成完成！")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
