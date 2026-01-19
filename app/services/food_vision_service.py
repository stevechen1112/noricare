import json
import os
from typing import Any, Dict

from PIL import Image
import google.generativeai as genai

from app.core.config import settings
from app.schemas.food_ai import FoodVisionResult


class FoodVisionService:
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("找不到 GEMINI_API_KEY，請檢查 .env 設定")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL_NAME)

    @staticmethod
    def _extract_first_json(text: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("empty response")
        start = text.find("{")
        if start == -1:
            raise ValueError("no json object found")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    snippet = text[start:i + 1]
                    return json.loads(snippet)
        raise ValueError("incomplete json object")

    def suggest_from_image(self, file_path: str, limit: int = 5) -> FoodVisionResult:
        img = Image.open(file_path)
        prompt = f"""
你是一位台灣營養師的助理。請從照片中辨識出主要食物/食材，並輸出純 JSON（不要 Markdown）。

請用以下 JSON 結構：
{{
  "food_candidates": [
    {{"name": "食物名稱", "confidence": 0.0-1.0, "hints": ["可選：如烤/炸/湯"]}}
  ],
  "ingredients": ["可選：成分/配料"],
  "cooking_method": "unknown/蒸/煮/炸/烤/炒/燉/涼拌",
  "warnings": ["可選：若看起來是加工食品/高糖高油等"]
}}

限制條件：
- 最多回傳 {limit} 個 food_candidates。
- 若不確定，請降低 confidence，但仍給可能候選。
"""
        response = self.model.generate_content([prompt, img])
        raw_text = response.text.strip() if response and response.text else ""
        data = self._extract_first_json(raw_text)
        return FoodVisionResult(**data)


food_vision_service = FoodVisionService()
