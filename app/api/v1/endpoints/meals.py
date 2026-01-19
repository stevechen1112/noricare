from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.all_models import AuthAccount, Meal, MealItem, User
from app.schemas.meal import (
    MealCreate,
    MealResponse,
    MealItemResponse,
    MealSummaryResponse,
    Nutrients,
    TodaySummaryResponse,
    TodayMealResponse,
    TodayMealItemResponse,
)
from app.services.food_alignment_service import get_food_alignment_service

router = APIRouter(prefix="/meals", tags=["Meals"])


def _scale_nutrients(per_100g: dict, grams: float) -> dict:
    factor = grams / 100.0
    return {
        "calories": round(per_100g.get("calories", 0) * factor, 4),
        "protein": round(per_100g.get("protein", 0) * factor, 4),
        "carbs": round(per_100g.get("carbs", 0) * factor, 4),
        "fat": round(per_100g.get("fat", 0) * factor, 4),
        "sodium": round(per_100g.get("sodium", 0) * factor, 4),
        "fiber": round(per_100g.get("fiber", 0) * factor, 4),
        "potassium": round(per_100g.get("potassium", 0) * factor, 4),
    }


def _sum_nutrients(items: List[dict]) -> dict:
    total = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "sodium": 0,
        "fiber": 0,
        "potassium": 0,
    }
    for n in items:
        for k in total:
            total[k] += n.get(k, 0)
    return {k: round(v, 4) for k, v in total.items()}


def _ensure_user_profile(db: Session, account: AuthAccount) -> User:
    if account.user_id:
        user = db.query(User).filter(User.id == account.user_id).first()
        if user:
            return user

    user = User(name=account.name)
    db.add(user)
    db.flush()
    account.user_id = user.id
    db.commit()
    db.refresh(account)
    return user


@router.post("", response_model=MealResponse)
async def create_meal(
    payload: MealCreate,
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    user = _ensure_user_profile(db, account)

    if not payload.items:
        raise HTTPException(status_code=400, detail="Meal items required")

    alignment_service = get_food_alignment_service()

    meal = Meal(
        user_id=user.id,
        source=payload.source or "manual",
        note=payload.note,
        eaten_at=payload.eaten_at or datetime.utcnow(),
    )
    db.add(meal)
    db.flush()

    item_responses: List[MealItemResponse] = []
    item_nutrients_list = []

    for item in payload.items:
        food = alignment_service.get_food_nutrients(item.food_id)
        if not food:
            raise HTTPException(status_code=404, detail=f"Food not found: {item.food_id}")

        nutrients = _scale_nutrients(food["per_100g"], item.grams)
        item_nutrients_list.append(nutrients)

        meal_item = MealItem(
            meal_id=meal.id,
            food_id=food["food_id"],
            food_name=food["name"],
            grams=item.grams,
            portion_label=item.portion_label,
            confidence=item.confidence,
            raw_text=item.raw_text,
            nutrients=nutrients,
        )
        db.add(meal_item)
        db.flush()

        item_responses.append(MealItemResponse(
            meal_item_id=meal_item.id,
            food_id=meal_item.food_id,
            food_name=meal_item.food_name,
            grams=meal_item.grams,
            portion_label=meal_item.portion_label,
            confidence=meal_item.confidence,
            nutrients=Nutrients(**nutrients),
        ))

    total_nutrients = _sum_nutrients(item_nutrients_list)
    meal.nutrients = total_nutrients

    db.commit()
    db.refresh(meal)

    return MealResponse(
        meal_id=meal.id,
        user_id=meal.user_id,
        eaten_at=meal.eaten_at,
        source=meal.source,
        note=meal.note,
        nutrients=Nutrients(**total_nutrients),
        items=item_responses,
    )


@router.get("", response_model=List[MealResponse])
async def list_meals(
    limit: int = Query(20, ge=1, le=100),
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    user = _ensure_user_profile(db, account)
    meals = (
        db.query(Meal)
        .filter(Meal.user_id == user.id)
        .order_by(Meal.eaten_at.desc())
        .limit(limit)
        .all()
    )

    responses: List[MealResponse] = []
    for meal in meals:
        item_responses: List[MealItemResponse] = []
        for item in meal.items:
            item_responses.append(MealItemResponse(
                meal_item_id=item.id,
                food_id=item.food_id,
                food_name=item.food_name,
                grams=item.grams,
                portion_label=item.portion_label,
                confidence=item.confidence,
                nutrients=Nutrients(**(item.nutrients or {})),
            ))

        responses.append(MealResponse(
            meal_id=meal.id,
            user_id=meal.user_id,
            eaten_at=meal.eaten_at,
            source=meal.source,
            note=meal.note,
            nutrients=Nutrients(**(meal.nutrients or {})),
            items=item_responses,
        ))

    return responses


@router.get("/summary", response_model=MealSummaryResponse)
async def meal_summary(
    days: int = Query(7, ge=1, le=365),
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    user = _ensure_user_profile(db, account)
    since = datetime.utcnow() - timedelta(days=days)
    meals = (
        db.query(Meal)
        .filter(Meal.user_id == user.id, Meal.eaten_at >= since)
        .order_by(Meal.eaten_at.asc())
        .all()
    )

    daily = {}
    total_items = []
    for meal in meals:
        day_key = meal.eaten_at.date().isoformat()
        daily.setdefault(day_key, [])
        nutrients = meal.nutrients or {}
        daily[day_key].append(nutrients)
        total_items.append(nutrients)

    daily_breakdown = []
    for day, items in daily.items():
        daily_breakdown.append({day: Nutrients(**_sum_nutrients(items))})

    total_nutrients = _sum_nutrients(total_items)

    return MealSummaryResponse(
        user_id=user.id,
        days=days,
        total_meals=len(meals),
        total_nutrients=Nutrients(**total_nutrients),
        daily_breakdown=daily_breakdown,
    )


@router.delete("/{meal_id}")
async def delete_meal(
    meal_id: str,
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    user = _ensure_user_profile(db, account)

    meal = (
        db.query(Meal)
        .filter(Meal.id == meal_id, Meal.user_id == user.id)
        .first()
    )
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    db.query(MealItem).filter(MealItem.meal_id == meal.id).delete(synchronize_session=False)
    db.delete(meal)
    db.commit()

    return {"status": "deleted", "meal_id": meal_id}


# ============================================================
# 今日統計 API (方案 B - 支援營養進度追蹤)
# ============================================================

@router.get("/summary/today", response_model=TodaySummaryResponse)
async def today_summary(
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    """
    取得今日飲食攝取統計
    
    返回今天 00:00 到目前為止的營養攝取總和
    用於 Meal Log 頁面的進度條顯示
    """
    user = _ensure_user_profile(db, account)
    
    # 取得今天的開始時間 (UTC 00:00)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    meals = (
        db.query(Meal)
        .filter(
            Meal.user_id == user.id, 
            Meal.eaten_at >= today_start
        )
        .order_by(Meal.eaten_at.asc())
        .all()
    )
    
    # 統計今日營養素
    total_items = [meal.nutrients or {} for meal in meals]
    total_nutrients = _sum_nutrients(total_items)
    
    # 整理每餐紀錄（用於顯示最近餐點）
    meals_list: List[TodayMealResponse] = []
    for meal in meals:
        items: List[TodayMealItemResponse] = []
        for item in meal.items:
            items.append(TodayMealItemResponse(
                food_name=item.food_name,
                grams=item.grams,
                portion_label=item.portion_label,
                nutrients=Nutrients(**(item.nutrients or {})),
            ))
        meals_list.append(TodayMealResponse(
            meal_id=meal.id,
            eaten_at=meal.eaten_at,
            source=meal.source,
            note=meal.note,
            nutrients=Nutrients(**(meal.nutrients or {})),
            items=items,
        ))
    
    return TodaySummaryResponse(
        user_id=user.id,
        date=today_start.date().isoformat(),
        total_meals=len(meals),
        total_nutrients=Nutrients(**total_nutrients),
        meals=meals_list,
    )
