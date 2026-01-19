from typing import List, Optional
from pydantic import BaseModel, Field


class FoodCandidate(BaseModel):
    name: str
    confidence: Optional[float] = None
    hints: Optional[List[str]] = None


class PortionEstimate(BaseModel):
    label: str = Field("unknown", description="bowl/plate/piece/cup/unknown")
    grams_range: Optional[List[float]] = None
    reference: Optional[str] = None


class FoodVisionResult(BaseModel):
    food_candidates: List[FoodCandidate]
    ingredients: Optional[List[str]] = None
    cooking_method: Optional[str] = "unknown"
    portion: Optional[PortionEstimate] = None
    warnings: Optional[List[str]] = None


class FoodLLMParseRequest(BaseModel):
    raw_response: str


class FoodDBMatch(BaseModel):
    food_id: str
    name: str
    category: str
    per_100g: dict


class FoodLLMParseResponse(BaseModel):
    parsed: FoodVisionResult
    db_match: Optional[FoodDBMatch] = None


class FoodVisionSuggestItem(BaseModel):
    name: str
    confidence: Optional[float] = None
    matched_food_id: Optional[str] = None
    matched_name: Optional[str] = None
    matched_category: Optional[str] = None
    estimated_grams: float
    grams_min: float
    grams_max: float
    estimate_label: str = Field("mid", description="mid/lower/upper")
    notes: Optional[str] = None


class FoodVisionSuggestResponse(BaseModel):
    items: List[FoodVisionSuggestItem]
    vision: Optional[FoodVisionResult] = None
