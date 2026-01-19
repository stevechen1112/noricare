"""
批量處理所有健檢報告圖片，整合完整數據後給出綜合建議
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

async def extract_from_image(image_path: str) -> dict:
    """從單張圖片提取數據"""
    img = Image.open(image_path)
    prompt = """
    你是一位專業的台灣醫事檢驗師，請從這張健檢報告圖片中提取所有檢驗指標。
    請以純 JSON 格式輸出（不要 Markdown）：
    {
      "fields": {
        "指標英文代號": {"value": 數值, "unit": "單位", "reference_range": "參考值", "status": "正常/偏高/偏低"}
      }
    }
    請提取所有可見的檢驗項目，包括但不限於：
    - 血液常規 (WBC, RBC, Hb, Hct, PLT, MCV, MCH, MCHC)
    - 肝功能 (ALT/GPT, AST/GOT, ALP, GGT, Albumin, Total Protein, Bilirubin)
    - 腎功能 (Creatinine, BUN, Uric Acid, eGFR)
    - 血糖 (Glucose, HbA1c)
    - 血脂 (TC, LDL, HDL, TG)
    - 甲狀腺 (TSH, T3, T4)
    - 電解質 (Na, K, Ca, Mg, P)
    - 尿液檢查
    - 腫瘤標記
    - 其他所有可見指標
    """
    
    response = model.generate_content([prompt, img])
    text = response.text.strip()
    
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    try:
        return json.loads(text)
    except:
        return {"fields": {}, "error": "解析失敗", "raw": text[:200]}

async def process_all_images():
    """批量處理所有圖片"""
    all_fields = {}
    
    images = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.jpg')])
    print(f"🔍 發現 {len(images)} 張健檢報告圖片\n")
    
    for img_name in images:
        img_path = os.path.join(DATA_DIR, img_name)
        print(f"📸 處理中: {img_name}...")
        
        result = await extract_from_image(img_path)
        fields = result.get("fields", {})
        
        print(f"   ✅ 提取 {len(fields)} 項指標")
        
        # 合併到總表（後面的會覆蓋前面重複的）
        for key, value in fields.items():
            all_fields[key] = value
    
    return all_fields

def analyze_complete_data(all_fields: dict, user_profile: dict) -> dict:
    """完整分析所有數據"""
    import math
    
    analysis = {
        "總指標數": len(all_fields),
        "異常項目": [],
        "正常項目": [],
        "計算指標": {},
        "風險評估": {}
    }
    
    age = user_profile.get("age", 40)
    is_male = user_profile.get("gender") == "male"
    
    # 分類所有指標
    for key, data in all_fields.items():
        if not isinstance(data, dict):
            continue
        status = (data.get("status") or "").lower()
        value = data.get("value")
        unit = data.get("unit") or ""
        ref = data.get("reference_range") or ""
        
        item_str = f"{key}: {value} {unit} (參考: {ref})"
        
        if "高" in status or "low" in status.lower() or "異常" in status:
            analysis["異常項目"].append(f"⚠️ {item_str}")
        elif "偏" in status:
            analysis["異常項目"].append(f"🟡 {item_str}")
        else:
            analysis["正常項目"].append(f"✅ {item_str}")
    
    # eGFR 計算
    crea_keys = ["CREATININE", "Creatinine", "CREA", "Cr", "肌酸酐"]
    for k in crea_keys:
        if k in all_fields:
            try:
                crea = float(all_fields[k]["value"])
                kappa = 0.9 if is_male else 0.7
                alpha = -0.302 if is_male else -0.241
                scr_kappa = crea / kappa
                egfr = 142 * (min(scr_kappa, 1.0) ** alpha) * (max(scr_kappa, 1.0) ** -1.200) * (0.9938 ** age) * (1.0 if is_male else 1.012)
                analysis["計算指標"]["eGFR"] = round(egfr, 1)
                
                if egfr >= 90:
                    analysis["計算指標"]["腎功能分期"] = "第一期：正常"
                elif egfr >= 60:
                    analysis["計算指標"]["腎功能分期"] = "第二期：輕度下降"
                elif egfr >= 45:
                    analysis["計算指標"]["腎功能分期"] = "第三期甲：中度下降"
                else:
                    analysis["計算指標"]["腎功能分期"] = "需關注"
                break
            except:
                pass
    
    # BMI 計算
    height_keys = ["HEIGHT", "Height", "身高"]
    weight_keys = ["WEIGHT", "Weight", "體重"]
    height = weight = None
    
    for k in height_keys:
        if k in all_fields:
            try:
                height = float(all_fields[k]["value"])
                break
            except:
                pass
    
    for k in weight_keys:
        if k in all_fields:
            try:
                weight = float(all_fields[k]["value"])
                break
            except:
                pass
    
    if height and weight:
        bmi = weight / ((height/100) ** 2)
        analysis["計算指標"]["BMI"] = round(bmi, 1)
        if bmi < 18.5:
            analysis["計算指標"]["體重狀態"] = "過輕"
        elif bmi < 24:
            analysis["計算指標"]["體重狀態"] = "正常"
        elif bmi < 27:
            analysis["計算指標"]["體重狀態"] = "過重"
        else:
            analysis["計算指標"]["體重狀態"] = "肥胖"
    
    # 風險評估
    risk_areas = {
        "心血管": [],
        "代謝": [],
        "肝臟": [],
        "腎臟": [],
        "血液": []
    }
    
    # 血糖風險
    for k in ["GLUCOSE", "Glucose", "GLU", "血糖", "AC Sugar"]:
        if k in all_fields:
            try:
                val = float(all_fields[k]["value"])
                if val >= 126:
                    risk_areas["代謝"].append(f"空腹血糖 {val} - 糖尿病範圍")
                elif val >= 100:
                    risk_areas["代謝"].append(f"空腹血糖 {val} - 前糖尿病")
                break
            except:
                pass
    
    # HbA1c
    for k in ["HbA1c", "HBA1C", "糖化血色素"]:
        if k in all_fields:
            try:
                val = float(all_fields[k]["value"])
                if val >= 6.5:
                    risk_areas["代謝"].append(f"HbA1c {val}% - 糖尿病範圍")
                elif val >= 5.7:
                    risk_areas["代謝"].append(f"HbA1c {val}% - 前糖尿病")
                break
            except:
                pass
    
    # 血脂
    lipid_checks = [
        ("LDL", "低密度膽固醇", 130),
        ("TC", "總膽固醇", 200),
        ("TG", "三酸甘油酯", 150),
    ]
    for k, name, threshold in lipid_checks:
        if k in all_fields:
            try:
                val = float(all_fields[k]["value"])
                if val > threshold:
                    risk_areas["心血管"].append(f"{name} {val} 偏高")
            except:
                pass
    
    # HDL (越高越好)
    if "HDL" in all_fields:
        try:
            val = float(all_fields["HDL"]["value"])
            if val < 40:
                risk_areas["心血管"].append(f"HDL {val} 偏低（保護因子不足）")
        except:
            pass
    
    # 肝功能
    liver_checks = [("ALT", 40), ("AST", 40), ("GPT", 40), ("GOT", 40), ("GGT", 50)]
    for k, threshold in liver_checks:
        if k in all_fields:
            try:
                val = float(all_fields[k]["value"])
                if val > threshold:
                    risk_areas["肝臟"].append(f"{k} {val} U/L 偏高")
            except:
                pass
    
    # 尿酸
    for k in ["URIC_ACID", "Uric Acid", "UA", "尿酸"]:
        if k in all_fields:
            try:
                val = float(all_fields[k]["value"])
                threshold = 7.0 if is_male else 6.0
                if val > threshold:
                    risk_areas["代謝"].append(f"尿酸 {val} 偏高（痛風風險）")
                break
            except:
                pass
    
    analysis["風險評估"] = {k: v for k, v in risk_areas.items() if v}
    
    return analysis

async def generate_comprehensive_advice(all_fields: dict, analysis: dict, user_profile: dict) -> str:
    """根據完整數據生成綜合建議"""
    
    prompt = f"""
    你是一位資深的台灣營養師，請根據這份完整的健康檢查報告，提供全面的個人化營養建議。

    【使用者基本資料】
    - 年齡: {user_profile.get('age', 40)} 歲
    - 性別: {'男性' if user_profile.get('gender') == 'male' else '女性'}
    - 健康目標: {user_profile.get('goal', '整體健康管理')}

    【完整檢驗數據 - 共 {len(all_fields)} 項指標】
    {json.dumps(all_fields, ensure_ascii=False, indent=2)}

    【系統分析摘要】
    - 計算指標: {json.dumps(analysis.get('計算指標', {}), ensure_ascii=False)}
    - 異常項目數: {len(analysis.get('異常項目', []))}
    - 風險評估: {json.dumps(analysis.get('風險評估', {}), ensure_ascii=False)}

    請提供：

    ## 1. 健康總評（100字內）
    針對整體數據給出專業評價

    ## 2. 重點關注項目
    列出最需要注意的 3-5 個指標，說明原因與影響

    ## 3. 營養改善策略
    針對每個異常項目，提供具體的飲食調整建議

    ## 4. 推薦食材清單
    列出 10 種最適合的台灣在地食材，標註其營養價值與對應改善的指標

    ## 5. 一週飲食計畫
    提供完整 7 天的三餐建議，包含具體食物與份量

    ## 6. 需要避免的食物
    明確列出應該減少或避免的食物類型

    ## 7. 生活型態建議
    運動、睡眠、壓力管理等輔助建議

    ## 8. 追蹤建議
    建議多久後複檢哪些項目

    請用繁體中文，語氣專業但親切。這是營養建議，不是醫療診斷。
    """
    
    response = model.generate_content(prompt)
    return response.text

async def main():
    print("=" * 70)
    print("🏥 Personal Health MVP - 完整數據整合分析")
    print("=" * 70)
    
    user_profile = {
        "age": 40,
        "gender": "male",
        "goal": "控制血糖、維持腎功能、整體健康管理"
    }
    
    # 階段1: 批量 OCR
    print("\n📋 【階段1】批量處理所有健檢報告圖片...")
    all_fields = await process_all_images()
    
    print(f"\n📊 總計提取 {len(all_fields)} 項不重複指標")
    
    # 階段2: 完整分析
    print("\n🔬 【階段2】完整數據分析...")
    analysis = analyze_complete_data(all_fields, user_profile)
    
    # 階段3: 綜合建議
    print("\n💡 【階段3】生成綜合營養建議...")
    advice = await generate_comprehensive_advice(all_fields, analysis, user_profile)
    
    # 輸出報告
    print("\n" + "=" * 70)
    print("📊 完整健康分析報告")
    print("=" * 70)
    
    print("\n【所有提取的檢驗指標】")
    print(json.dumps(all_fields, ensure_ascii=False, indent=2))
    
    print("\n【分析摘要】")
    print(f"總指標數: {analysis['總指標數']}")
    print(f"計算指標: {json.dumps(analysis['計算指標'], ensure_ascii=False)}")
    
    print("\n【異常項目】")
    for item in analysis["異常項目"]:
        print(f"  {item}")
    
    print("\n【風險評估】")
    for area, risks in analysis["風險評估"].items():
        if risks:
            print(f"  {area}:")
            for r in risks:
                print(f"    - {r}")
    
    print("\n" + "=" * 70)
    print("📝 營養師綜合建議")
    print("=" * 70)
    print(advice)
    
    print("\n" + "=" * 70)
    print("✅ 完整分析完成！")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
