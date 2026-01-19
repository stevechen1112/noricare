"""
Personal Health MVP - 完整流程演示
從圖片 → OCR → 分析 → 營養建議 (End-to-End)
"""
import asyncio
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()

# ============ 配置 ============
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-3-pro-preview")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=GEMINI_MODEL)

# ============ 階段1: OCR 提取 ============
async def extract_health_data(image_path: str) -> dict:
    """從健檢報告圖片提取結構化數據"""
    print(f"📸 正在處理圖片: {os.path.basename(image_path)}")
    
    img = Image.open(image_path)
    prompt = """
    你是一位專業的台灣醫事檢驗師，請從這張健檢報告圖片中提取所有檢驗指標。
    請以純 JSON 格式輸出（不要 Markdown）：
    {
      "fields": {
        "指標英文代號": {"value": 數值, "unit": "單位", "reference_range": "參考值"}
      },
      "report_date": "YYYY-MM-DD"
    }
    重點提取：肝功能(ALT/AST)、腎功能(Creatinine/BUN)、血糖(Glucose/HbA1c)、血脂(TC/LDL/HDL/TG)、尿酸、血壓等。
    """
    
    response = model.generate_content([prompt, img])
    text = response.text.strip()
    
    # 清理 JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    return json.loads(text)

# ============ 階段2: 健康分析 ============
import math

def calculate_egfr(creatinine: float, age: int, is_male: bool) -> float:
    """CKD-EPI 2021 公式"""
    kappa = 0.9 if is_male else 0.7
    alpha = -0.302 if is_male else -0.241
    scr_kappa = creatinine / kappa
    egfr = 142 * (min(scr_kappa, 1.0) ** alpha) * (max(scr_kappa, 1.0) ** -1.200) * (0.9938 ** age) * (1.0 if is_male else 1.012)
    return round(egfr, 1)

def analyze_health(ocr_data: dict, user_profile: dict) -> dict:
    """分析健康數據並生成風險評估"""
    fields = ocr_data.get("fields", {})
    analysis = {
        "原始指標": fields,
        "計算指標": {},
        "異常項目": [],
        "風險等級": "低"
    }
    
    age = user_profile.get("age", 40)
    is_male = user_profile.get("gender") == "male"
    
    # eGFR 計算
    crea = None
    for key in ["Creatinine", "CREA", "肌酸酐", "Cr"]:
        if key in fields:
            crea = fields[key].get("value")
            break
    
    if crea:
        egfr = calculate_egfr(float(crea), age, is_male)
        analysis["計算指標"]["eGFR"] = f"{egfr} ml/min/1.73m²"
        if egfr < 60:
            analysis["異常項目"].append(f"⚠️ 腎功能下降 (eGFR={egfr})")
            analysis["風險等級"] = "高"
    
    # 血糖判讀
    glucose = None
    for key in ["Glucose", "GLU", "血糖", "AC Sugar"]:
        if key in fields:
            glucose = fields[key].get("value")
            break
    
    if glucose:
        glucose = float(glucose)
        if glucose >= 126:
            analysis["異常項目"].append(f"🔴 空腹血糖過高 ({glucose} mg/dL) - 糖尿病範圍")
            analysis["風險等級"] = "高"
        elif glucose >= 100:
            analysis["異常項目"].append(f"🟡 空腹血糖偏高 ({glucose} mg/dL) - 糖尿病前期")
            if analysis["風險等級"] == "低":
                analysis["風險等級"] = "中"
    
    # 血脂判讀
    for key, name, threshold in [("LDL", "低密度膽固醇", 130), ("TG", "三酸甘油酯", 150), ("TC", "總膽固醇", 200)]:
        if key in fields:
            val = float(fields[key].get("value", 0))
            if val > threshold:
                analysis["異常項目"].append(f"🟡 {name}偏高 ({val})")
    
    # 肝功能
    for key, name, threshold in [("ALT", "GPT", 40), ("AST", "GOT", 40)]:
        if key in fields:
            val = float(fields[key].get("value", 0))
            if val > threshold:
                analysis["異常項目"].append(f"🟡 肝指數{name}偏高 ({val} U/L)")
    
    return analysis

# ============ 階段3: AI 營養建議 ============
async def generate_recommendations(analysis: dict, user_profile: dict) -> str:
    """根據健康分析結果生成個人化營養建議"""
    
    prompt = f"""
    你是一位專業的台灣營養師，請根據以下健康檢查分析結果，提供具體且實用的營養建議。

    【使用者基本資料】
    - 年齡: {user_profile.get('age', '未知')} 歲
    - 性別: {'男性' if user_profile.get('gender') == 'male' else '女性'}
    - 目標: {user_profile.get('goal', '維持健康')}

    【健康分析結果】
    - 計算指標: {json.dumps(analysis.get('計算指標', {}), ensure_ascii=False)}
    - 異常項目: {analysis.get('異常項目', [])}
    - 整體風險等級: {analysis.get('風險等級', '低')}

    【原始檢驗數據】
    {json.dumps(analysis.get('原始指標', {}), ensure_ascii=False, indent=2)}

    請提供：
    1. **整體健康摘要** (2-3句話)
    2. **飲食建議** (針對異常項目的具體食物建議，包含台灣常見食材)
    3. **推薦食材清單** (列出 5-8 種適合的食材，標註營養價值)
    4. **一週菜單範例** (早/午/晚餐各一個簡單範例)
    5. **注意事項** (需要避免的食物或習慣)

    請用繁體中文回答，語氣親切但專業。不要提供醫療診斷，僅限營養建議。
    """
    
    response = model.generate_content(prompt)
    return response.text

# ============ 主流程 ============
async def run_mvp_pipeline():
    print("=" * 60)
    print("🏥 Personal Health MVP - 完整流程演示")
    print("=" * 60)
    
    # 使用者基本資料 (之後可改成問卷輸入)
    user_profile = {
        "age": 40,
        "gender": "male",
        "goal": "控制血糖、維持腎功能健康"
    }
    
    # 測試圖片路徑
    test_image = r"C:\Users\User\Desktop\personalhealth\steve_personaldata\40108.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ 找不到測試圖片: {test_image}")
        return
    
    # 階段1: OCR
    print("\n📋 【階段1】OCR 數據提取...")
    ocr_data = await extract_health_data(test_image)
    print(f"   ✅ 成功提取 {len(ocr_data.get('fields', {}))} 項指標")
    
    # 階段2: 分析
    print("\n🔬 【階段2】健康數據分析...")
    analysis = analyze_health(ocr_data, user_profile)
    print(f"   ✅ 風險等級: {analysis['風險等級']}")
    if analysis["異常項目"]:
        print("   📌 發現異常項目:")
        for item in analysis["異常項目"]:
            print(f"      {item}")
    
    # 階段3: 建議
    print("\n💡 【階段3】生成個人化營養建議...")
    recommendations = await generate_recommendations(analysis, user_profile)
    
    print("\n" + "=" * 60)
    print("📊 完整分析報告")
    print("=" * 60)
    
    print("\n【原始 OCR 數據】")
    print(json.dumps(ocr_data, ensure_ascii=False, indent=2))
    
    print("\n【健康分析摘要】")
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    
    print("\n【營養師建議】")
    print(recommendations)
    
    print("\n" + "=" * 60)
    print("✅ MVP 流程完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_mvp_pipeline())
