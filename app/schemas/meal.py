from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class Nutrients(BaseModel):
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    sodium: float = 0
    fiber: float = 0
    potassium: float = 0


class MealItemCreate(BaseModel):
    food_id: str = Field(..., description="資料庫整合編號")
    grams: float = Field(..., gt=0)
    portion_label: Optional[str] = None
    confidence: Optional[float] = None
    raw_text: Optional[str] = None


class MealCreate(BaseModel):
    user_id: Optional[str] = None
    items: List[MealItemCreate]
    source: Optional[str] = "manual"
    note: Optional[str] = None
    eaten_at: Optional[datetime] = None


class MealItemResponse(BaseModel):
    meal_item_id: str
    food_id: str
    food_name: str
    grams: float
    portion_label: Optional[str]
    confidence: Optional[float]
    nutrients: Nutrients


class MealResponse(BaseModel):
    meal_id: str
    user_id: str
    eaten_at: datetime
    source: str
    note: Optional[str]
    nutrients: Nutrients
    items: List[MealItemResponse]


class MealSummaryResponse(BaseModel):
    user_id: str
    days: int
    total_meals: int
    total_nutrients: Nutrients
    daily_breakdown: List[Dict[str, Nutrients]]


class TodayMealItemResponse(BaseModel):
    food_name: str
    grams: float
    portion_label: Optional[str]
    nutrients: Nutrients


class TodayMealResponse(BaseModel):
    meal_id: str
    eaten_at: Optional[datetime]
    source: str
    note: Optional[str]
    nutrients: Nutrients
    items: List[TodayMealItemResponse]


class TodaySummaryResponse(BaseModel):
    user_id: str
    date: str
    total_meals: int
    total_nutrients: Nutrients
    meals: List[TodayMealResponse]
