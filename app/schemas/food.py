from typing import List
from pydantic import BaseModel, Field


class FoodMatch(BaseModel):
    food_id: str = Field(..., description="資料庫整合編號")
    name: str
    category: str
    matched_field: str
    score: float


class FoodAlignResponse(BaseModel):
    query: str
    count: int
    results: List[FoodMatch]
