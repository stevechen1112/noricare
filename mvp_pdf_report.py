import asyncio
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

load_dotenv()

# ============ AI Configuration ============
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-3-pro-preview")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=GEMINI_MODEL)

# ============ Data ============
USER_PROFILE = {
    "name": "Steve",
    "age": 40,
    "gender": "male",
    "height_cm": 178.8,
    "weight_kg": 78.8,
    "goal": "控制血糖、維持腎功能、整體健康管理"
}

HEALTH_DATA = {
    "GLUCOSE": {"value": 117.0, "unit": "mg/dL", "reference_range": "70-99", "status": "Fail"},
    "HbA1c": {"value": 5.8, "unit": "%", "reference_range": "4.0-5.6", "status": "Fail"},
    "Glucose_PC": {"value": 169, "unit": "mg/dL", "reference_range": "<140", "status": "Fail"},
    "Creatinine": {"value": 1.05, "unit": "mg/dL", "reference_range": "0.7-1.2", "status": "Pass"},
    "eGFR": {"value": 92, "unit": "mL/min/1.73m²", "reference_range": ">60", "status": "Pass"},
    "BUN": {"value": 16, "unit": "mg/dL", "reference_range": "7-20", "status": "Pass"},
    "AST/GOT": {"value": 38, "unit": "U/L", "reference_range": "<40", "status": "Pass"},
    "ALT/GPT": {"value": 32, "unit": "U/L", "reference_range": "<40", "status": "Pass"},
    "Systolic_BP": {"value": 119, "unit": "mmHg", "reference_range": "<120", "status": "Pass"},
    "Diastolic_BP": {"value": 71, "unit": "mmHg", "reference_range": "<80", "status": "Pass"},
    "BMI": {"value": 24.6, "unit": "kg/m²", "reference_range": "18.5-24", "status": "Fail"},
    "Hb": {"value": 14.3, "unit": "g/dL", "reference_range": "13.5-17.5", "status": "Pass"},
    "Na": {"value": 138, "unit": "mEq/L", "reference_range": "135-145", "status": "Pass"},
    "K": {"value": 4.3, "unit": "mEq/L", "reference_range": "3.5-5.1", "status": "Pass"},
    "Calcium": {"value": 8.9, "unit": "mg/dL", "reference_range": "8.6-10.2", "status": "Pass"},
}

ABNORMAL_ITEMS = [
    "空腹血糖 117 mg/dL (偏高，糖尿病前期)",
    "HbA1c 5.8% (偏高，糖尿病前期)",
    "飯後血糖 169 mg/dL (顯著偏高)",
    "BMI 24.6 (過重，需減重約 4-5 公斤)"
]

# ============ Helper Functions ============

def register_chinese_font():
    """Tries to register a Chinese font (Microsoft JhengHei)."""
    font_path = r"C:\Windows\Fonts\msjh.ttc"
    font_name = "MsJhengHei"
    try:
        if os.path.exists(font_path):
            # For TTC, we need subfontIndex. 0 is usually Light/Regular.
            pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
            return font_name
    except Exception as e:
        print(f"Font registration failed for {font_path}: {e}")
    
    # Fallback to SimHei if msjh fails (often on some systems)
    try:
        font_path = r"C:\Windows\Fonts\simhei.ttf"
        if os.path.exists(font_path):
             pdfmetrics.registerFont(TTFont("SimHei", font_path))
             return "SimHei"
    except:
        pass
        
    print("Warning: No Chinese font found. PDF characters may not render.")
    return "Helvetica"

def parse_markdown_to_flowables(text, styles):
    """Parses simple Markdown to ReportLab flowables."""
    flowables = []
    lines = text.split('\n')
    
    # Custom styles
    h1 = styles['Heading1']
    h2 = styles['Heading2']
    h3 = styles['Heading3']
    normal = styles['Normal']
    
    current_list_items = []

    for line in lines:
        line = line.strip()
        if not line:
             continue
        
        # Replace **bold** with <b>bold</b> (ReportLab tags)
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        
        if line.startswith('# '):
            flowables.append(Paragraph(line[2:], h1))
        elif line.startswith('## '):
            flowables.append(Spacer(1, 10))
            flowables.append(Paragraph(line[3:], h2))
        elif line.startswith('### '):
            flowables.append(Spacer(1, 5))
            flowables.append(Paragraph(line[4:], h3))
        elif line.startswith('- ') or line.startswith('* '):
             # Bullet points
             flowables.append(Paragraph(f"• {line[2:]}", normal))
        else:
             flowables.append(Paragraph(line, normal))
             
    return flowables

# ============ Generation Functions (Reusing logic) ============

async def generate_full_advice():
    """Generates all advice parts."""
    
    # Food Prompt
    food_prompt = f"""
    Please provide food intake advice for a 40-year-old male with Pre-diabetes and BMI 24.6.
    Abnormal data: {ABNORMAL_ITEMS}.
    Full Data: {json.dumps(HEALTH_DATA)}.
    Output in strictly formatted Markdown. Use Traditional Chinese (繁體中文).
    Structure:
    # 🥗 每日食物攝取建議
    ## 1. 主食類
    ## 2. 蛋白質類
    ## 3. 蔬菜類
    ## 4. 水果類
    ## 5. 油脂與飲品
    """
    
    # Supplement Prompt
    supp_prompt = f"""
    Please provide supplement advice for a 40-year-old male with Pre-diabetes.
    Safety: eGFR 92 (Normal kidney).
    Full Data: {json.dumps(HEALTH_DATA)}.
    Output in strictly formatted Markdown. Use Traditional Chinese (繁體中文).
    Structure:
    # 💊 保健食品建議
    ## 🔴 優先建議
    ## 🟡 輔助建議
    ## ⚠️ 安全提醒
    """
    
    # Meal Plan Prompt
    meal_prompt = f"""
    Create a 7-day meal plan for blood sugar control and weight loss.
    Target: 1800-2000 kcal/day.
    Output in strictly formatted Markdown. Use Traditional Chinese (繁體中文).
    Structure:
    # 🍽️ 一週菜單計畫
    ## 週一
    ## 週二
    ...
    ## 週日
    """
    
    print("Generating AI content... (This may take a minute)")
    
    # Run in parallel for speed in real app, but sequential is safer for rate limits
    food_res = await model.generate_content_async(food_prompt)
    supp_res = await model.generate_content_async(supp_prompt)
    meal_res = await model.generate_content_async(meal_prompt)
    
    return food_res.text, supp_res.text, meal_res.text

# ============ PDF Creation ============

async def create_pdf():
    chinese_font = register_chinese_font()
    
    doc = SimpleDocTemplate("Steve_Health_Report.pdf", pagesize=A4,
                            rightMargin=40, leftMargin=40, 
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    # Define Chinese styles
    styles.add(ParagraphStyle(name='ChineseTitle', fontName=chinese_font, fontSize=24, leading=30, alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name='ChineseH1', fontName=chinese_font, fontSize=18, leading=22, spaceAfter=10, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='ChineseH2', fontName=chinese_font, fontSize=14, leading=18, spaceAfter=8, textColor=colors.teal))
    styles.add(ParagraphStyle(name='ChineseH3', fontName=chinese_font, fontSize=12, leading=15, spaceAfter=6, textColor=colors.black))
    styles.add(ParagraphStyle(name='ChineseBody', fontName=chinese_font, fontSize=10, leading=14, spaceAfter=4))
    styles.add(ParagraphStyle(name='ChineseRed', fontName=chinese_font, fontSize=10, leading=14, textColor=colors.red))
    
    # Map for parser
    style_map = {
        'Heading1': styles['ChineseH1'],
        'Heading2': styles['ChineseH2'],
        'Heading3': styles['ChineseH3'],
        'Normal': styles['ChineseBody'],
        'BodyText': styles['ChineseBody']
    }
    
    elements = []
    
    # --- Cover Page ---
    elements.append(Spacer(1, 60))
    elements.append(Paragraph("個人健康數據分析報告", styles['ChineseTitle']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"受測者: {USER_PROFILE['name']}", styles['ChineseH2']))
    elements.append(Paragraph(f"日期: {datetime.now().strftime('%Y-%m-%d')}", styles['ChineseH2']))
    elements.append(Spacer(1, 20))
    
    # --- Health Assessment Score (Visual) ---
    # Simplified Score concept
    score = 75 # Based on finding pre-diabetes but good organ function
    elements.append(Paragraph(f"綜合健康評分: {score}/100", styles['ChineseH1']))
    elements.append(Spacer(1, 20))
    
    # --- Summary Table ---
    elements.append(Paragraph("1. 主要異常項目摘要", styles['ChineseH1']))
    for item in ABNORMAL_ITEMS:
        elements.append(Paragraph(f"• {item}", styles['ChineseRed']))
    elements.append(Spacer(1, 20))
    
    # --- Detailed Data Table ---
    elements.append(Paragraph("2. 完整檢驗數據", styles['ChineseH1']))
    
    table_data = [["檢驗項目 (Item)", "數值 (Value)", "參考值 (Ref)", "狀態 (Status)"]]
    
    for key, data in HEALTH_DATA.items():
        # Clean status for display
        status_text = "異常" if data['status'] == 'Fail' or data['status'] == '偏高' or data['status'] == '過重' else "正常"
        row = [key, f"{data['value']} {data['unit']}", data['reference_range'], status_text]
        table_data.append(row)
        
    t = Table(table_data, colWidths=[150, 150, 100, 80])
    
    # Table Style
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font), # Use Chinese font for content
    ]))
    
    # Highlight abnormal rows
    for i, row in enumerate(table_data[1:], start=1):
        if row[3] == "異常":
            t.setStyle(TableStyle([
                ('TEXTCOLOR', (3, i), (3, i), colors.red),
                ('FONTNAME', (3, i), (3, i), f"{chinese_font}") 
            ]))
            
    elements.append(t)
    elements.append(PageBreak())
    
    # --- AI Analysis Content ---
    food_text, supp_text, meal_text = await generate_full_advice()
    
    # Food
    elements.extend(parse_markdown_to_flowables(food_text, style_map))
    elements.append(PageBreak())
    
    # Supplements
    elements.extend(parse_markdown_to_flowables(supp_text, style_map))
    elements.append(PageBreak())
    
    # Meal Plan
    elements.extend(parse_markdown_to_flowables(meal_text, style_map))
    
    # Build
    doc.build(elements)
    print("PDF Generated: Steve_Health_Report.pdf")

if __name__ == "__main__":
    asyncio.run(create_pdf())
