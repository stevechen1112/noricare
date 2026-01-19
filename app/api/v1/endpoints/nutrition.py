"""
Nutrition Database API Endpoints (Phase 1 MVP)
===============================================
獨立的營養查詢 API，完全隔離於現有 AI 報告流程。

端點設計：
- GET /nutrition/search?q=雞胸肉 - 搜尋食物
- GET /nutrition/calculate?food=雞胸肉&grams=150 - 計算營養
- GET /nutrition/categories - 取得分類列表
- GET /nutrition/stats - 服務統計（含匹配率）
- GET /nutrition/validate - 驗證 Top 20 匹配率

隔離策略：
- 此 API 失敗不會影響 /recommendation 等核心功能
- 可獨立測試、獨立部署
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.services.nutrition_db_service import get_nutrition_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


# ============ Response Models ============

class NutrientsPer100g(BaseModel):
    """每 100g 營養成分"""
    calories: float
    protein: float
    carbs: float
    fat: float
    sodium: float
    fiber: float
    potassium: float


class FoodNutrition(BaseModel):
    """食物營養資訊"""
    name: str
    category: str
    per_100g: NutrientsPer100g


class CalculatedNutrients(BaseModel):
    """計算後的營養成分"""
    name: str
    grams: float
    nutrients: NutrientsPer100g


class SearchResponse(BaseModel):
    """搜尋結果"""
    query: str
    count: int
    results: List[FoodNutrition]


class StatsResponse(BaseModel):
    """統計資訊"""
    total_foods: int
    total_categories: int
    match_rate_percent: float
    status: str


class ValidationResult(BaseModel):
    """驗證結果（單項）"""
    query: str
    matched: bool
    matched_name: Optional[str]


class ValidationResponse(BaseModel):
    """Top 20 驗證結果"""
    test_count: int
    matched_count: int
    match_rate_percent: float
    target_rate_percent: float
    passed: bool
    details: List[ValidationResult]


# ============ Endpoints ============

@router.get("/search", response_model=SearchResponse)
async def search_food(
    q: str = Query(..., min_length=1, description="食物名稱"),
    limit: int = Query(5, ge=1, le=20, description="回傳筆數上限"),
    category: Optional[str] = Query(None, description="限定食品分類")
):
    """
    搜尋食物營養資訊
    
    支援：
    - 精確匹配：「白飯」
    - 別名匹配：「白飯」→「蓬萊米飯」
    - 模糊匹配：「雞」→「雞胸肉」、「雞腿」...
    
    範例：
    - /nutrition/search?q=雞胸肉
    - /nutrition/search?q=豆腐&category=豆類
    """
    try:
        service = get_nutrition_service()
        results = service.search(q, limit=limit, category=category)
        
        return SearchResponse(
            query=q,
            count=len(results),
            results=[FoodNutrition(**r) for r in results]
        )
    except Exception as e:
        logger.error(f"搜尋失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")


@router.get("/calculate")
async def calculate_nutrients(
    food: str = Query(..., min_length=1, description="食物名稱"),
    grams: float = Query(100, gt=0, le=10000, description="克數")
):
    """
    計算指定克數的營養成分
    
    範例：
    - /nutrition/calculate?food=白飯&grams=200
    - /nutrition/calculate?food=雞胸肉&grams=150
    """
    try:
        service = get_nutrition_service()
        result = service.calculate_nutrients(food, grams)
        
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail=f"找不到食物：{food}"
            )
        
        return CalculatedNutrients(
            name=result['name'],
            grams=result['grams'],
            nutrients=NutrientsPer100g(**result['nutrients'])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"計算失敗: {e}")
        raise HTTPException(status_code=500, detail=f"計算失敗: {str(e)}")


@router.get("/categories", response_model=List[str])
async def get_categories():
    """取得所有食品分類列表"""
    try:
        service = get_nutrition_service()
        return service.get_categories()
    except Exception as e:
        logger.error(f"取得分類失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取得分類失敗: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    取得服務統計資訊
    
    包含：
    - 總食物數
    - 總分類數
    - 查詢匹配率
    - 服務狀態
    """
    try:
        service = get_nutrition_service()
        stats = service.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"取得統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取得統計失敗: {str(e)}")


@router.get("/validate", response_model=ValidationResponse)
async def validate_top20():
    """
    驗證 Top 20 常見食物的匹配率
    
    這是 Phase 1 的核心成功指標：
    - 目標：匹配率 ≥ 80%
    - 測試食物包含主食、蛋白質、蔬菜、水果各類
    
    若 passed=true，表示資料庫整合有效
    若 passed=false，需要擴充別名映射表
    """
    try:
        service = get_nutrition_service()
        result = service.validate_top20_foods()
        return ValidationResponse(**result)
    except Exception as e:
        logger.error(f"驗證失敗: {e}")
        raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}")


@router.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        service = get_nutrition_service()
        stats = service.get_stats()
        return {
            "status": "ok" if stats['status'] == 'healthy' else "degraded",
            "total_foods": stats['total_foods'],
            "message": "Nutrition DB service is running"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
