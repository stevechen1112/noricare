import os
import time
import json
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class OCRService:
    def __init__(self):
        # 初始化 Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("找不到 GEMINI_API_KEY，請檢查 .env 檔案")
            
        genai.configure(api_key=api_key)
        # 使用使用者指定的模型名稱
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")
        self.model = genai.GenerativeModel(model_name=self.model_name)

    async def process_image(self, file_path: str):
        """
        使用 Gemini 進行 OCR 與結構化數據提取 (Sprint 2)
        """
        print(f"DEBUG: 正在使用 {self.model_name} 處理圖片 {file_path}")
        
        try:
            img = Image.open(file_path)
            
            prompt = """
            你是一位專業的台灣醫事檢驗師，請從這張健檢報告圖片中提取所有檢驗指標。
            請以此 JSON 格式輸出，不要包含任何 Markdown 區塊或額外解釋：
            {
              "fields": {
                "指標名稱(英文代號)": {
                  "value": 數值,
                  "unit": "單位",
                  "reference_range": "參考值",
                  "status": "Normal/High/Low/Pass/Fail",
                  "confidence": 0-1 信心分數
                }
              },
              "metadata": {
                "report_date": "YYYY-MM-DD",
                "hospital": "醫院名稱"
              }
            }
            
            請專注於提取：
            1. 肝功能 (ALT/GPT, AST/GOT)
            2. 腎功能 (Creatinine, eGFR)
            3. 血糖 (HbA1c, Glucose)
            4. 血脂 (TC, LDL, HDL, TG)
            
            如果指標不存在，請忽略該欄位。
            """
            
            response = self.model.generate_content([prompt, img])
            
            # 清理回應內容，確保是純 JSON
            text_response = response.text.strip()
            if "```json" in text_response:
                text_response = text_response.split("```json")[1].split("```")[0].strip()
            elif "```" in text_response:
                text_response = text_response.split("```")[1].split("```")[0].strip()
                
            result_data = json.loads(text_response)
            
            # 確保內容是字典格式
            if not isinstance(result_data, dict):
                raise ValueError("AI 回傳格式不正確（預期為 JSON 對象）")
            
            # 補充 metadata
            if "metadata" not in result_data:
                result_data["metadata"] = {}
            result_data["metadata"]["source"] = os.path.basename(file_path)
            result_data["metadata"]["processed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 轉換為前端期望的格式
            formatted_result = {
                "structured_data": result_data.get("fields", {}),
                "abnormal_items": self._extract_abnormal_items(result_data.get("fields", {})),
                "metadata": result_data.get("metadata", {})
            }
            
            return formatted_result
            
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return {
                "status": "error",
                "message": f"Gemini OCR 處理失敗: {str(e)}",
                "raw_response": response.text if 'response' in locals() else None
            }
    
    def _extract_abnormal_items(self, fields: dict) -> list:
        """
        從檢驗數據中提取異常項目
        """
        abnormal_items = []
        
        # 簡單的異常檢測規則（可以根據需要擴展）
        abnormal_rules = {
            "ALT": (0, 40),
            "GPT": (0, 40),
            "AST": (0, 40),
            "GOT": (0, 40),
            "Creatinine": (0.6, 1.3),
            "肌酸酐": (0.6, 1.3),
            "HbA1c": (4.0, 5.6),
            "糖化血色素": (4.0, 5.6),
            "Glucose": (70, 100),
            "血糖": (70, 100),
            "TC": (0, 200),
            "LDL": (0, 130),
            "HDL": (40, 1000),
            "TG": (0, 150),
            "三酸甘油酯": (0, 150)
        }
        
        for field_name, field_data in fields.items():
            if not isinstance(field_data, dict):
                continue
            
            value = field_data.get("value")
            if value is None:
                continue
            
            try:
                value = float(value)
                # 檢查是否在異常規則中
                for rule_name, (min_val, max_val) in abnormal_rules.items():
                    if rule_name.lower() in field_name.lower():
                        if value < min_val or value > max_val:
                            abnormal_items.append({
                                "name": field_name,
                                "value": value,
                                "unit": field_data.get("unit", ""),
                                "reference_range": field_data.get("reference_range", f"{min_val}-{max_val}"),
                                "status": "high" if value > max_val else "low"
                            })
                        break
            except (ValueError, TypeError):
                continue
        
        return abnormal_items

ocr_service = OCRService()
