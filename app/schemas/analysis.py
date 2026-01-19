from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class HealthMetricStatus(BaseModel):
    value: float | str | None = None
    unit: str | None = ""
    reference_range: str | None = "N/A"
    status: str | None = "Normal"  # Normal, Fail, Warning, High, Low
    confidence: float | None = 0.0

class OCROutput(BaseModel):
    """原始 OCR 識別結果"""
    raw_text: Optional[str] = None
    structured_data: Dict[str, HealthMetricStatus] = Field(default_factory=dict)
    abnormal_items: List[str] = Field(default_factory=list)

class AnalysisRequest(BaseModel):
    """前端請求分析的 Payload"""
    user_id: str
    image_ids: List[str]  # 支援多張圖表同時分析
    # 可選：這次分析是否要帶入特定的當下情境？
    current_context: Optional[str] = None 

class AdviceSection(BaseModel):
    title: str
    content: str
    action_items: List[str] = Field(default_factory=list)

class NutritionReport(BaseModel):
    """最終產出的完整報告結構"""
    report_id: str
    created_at: str
    health_score: Optional[int] = None
    
    # 這是為了前端 UI 好的呈現，將大段文字結構化
    food_advice: List[AdviceSection]
    supplement_advice: List[AdviceSection]
    meal_plan: Dict[str, Any] # 週一到週日
    
    # 原始數據備份
    health_data_snapshot: Dict[str, HealthMetricStatus]
