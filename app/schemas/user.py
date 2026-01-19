from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# 為了未來的 UI/UX 設計，我們將使用者畫像定義得更細緻
class UserLifestyle(BaseModel):
    dietary_preference: Optional[str] = Field(None, description="飲食偏好 (如: 素食、生酮)")
    allergies: List[str] = Field(default_factory=list, description="過敏原清單")
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = Field(
        "sedentary", description="活動量 (久坐/輕度/中度/活躍/高度活躍)"
    )
    eating_habits: List[str] = Field(default_factory=list, description="飲食習慣標籤 (如: 外食族, 不吃早餐, 只有超商可選)")
    budget_level: Optional[str] = Field(None, description="預算等級，用來決定推薦平價還是高價保健品")

class UserProfileBase(BaseModel):
    name: str = Field(..., example="Steve")
    age: int = Field(..., gt=0, lt=120)
    gender: Literal["male", "female", "other"]
    height_cm: float = Field(..., gt=50, lt=300)
    weight_kg: float = Field(..., gt=20, lt=500)
    health_goals: List[str] = Field(default_factory=list, description="健康目標 (如: 減重, 增肌, 控糖)")
    
    # 這是為了未來性加入的欄位
    lifestyle: Optional[UserLifestyle] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: str
    bmi: float

    class Config:
        from_attributes = True

from typing import Dict, Any

class HealthRecordHistoryItem(BaseModel):
    record_id: str
    created_at: str
    health_score: Optional[int]
    # 簡化版的數據，僅用於圖表 (Key: Value)
    key_metrics: Dict[str, float]

class UserHistoryResponse(BaseModel):
    user_id: str
    history: List[HealthRecordHistoryItem]


class DashboardKeyMetric(BaseModel):
    label: str
    value: float | str | None
    unit: Optional[str] = None
    status: str = "normal"  # normal|caution|warning|danger


class DashboardAbnormalItem(BaseModel):
    name: str
    value: float | str | None
    unit: Optional[str] = None
    severity: str = "warning"  # caution|warning|danger
    normal_range: Optional[str] = None


class UserDashboardResponse(BaseModel):
    user_id: str
    latest_record_date: Optional[str]
    health_score: Optional[int]
    key_metrics: List[DashboardKeyMetric]
    abnormal_items: List[DashboardAbnormalItem]
    history: List[HealthRecordHistoryItem]
    # 新增：AI 分析報告內容（持久化）
    ai_report: Optional[Dict[str, Any]] = None
