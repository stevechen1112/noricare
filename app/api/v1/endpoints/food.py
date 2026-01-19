import json
import os
import shutil
from uuid import uuid4
from fastapi import APIRouter, Query, HTTPException, UploadFile, File
import logging

from app.schemas.food import FoodAlignResponse, FoodMatch
from app.schemas.food_ai import (
    FoodLLMParseRequest,
    FoodLLMParseResponse,
    FoodDBMatch,
    FoodVisionResult,
    FoodVisionSuggestResponse,
    FoodVisionSuggestItem,
)
from app.services.food_alignment_service import get_food_alignment_service
from app.services.food_vision_service import food_vision_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/food", tags=["Food"])

UPLOAD_DIR = "uploads"


def _extract_first_json(text: str) -> dict:
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


def _estimate_grams_by_category(category: str | None, profile: str = "bento") -> tuple[float, float, float, str]:
    # Nutritionist-oriented, practical presets.
    # bento: 台式便當/一般外食（主食偏多、整體偏中等份量）
    # fitness: 健身高蛋白（蛋白質偏多、主食偏可控、蔬菜偏多）
    ranges_by_profile: dict[str, dict[str, tuple[float, float]]] = {
        "bento": {
            "穀物類": (180, 350),
            "澱粉類": (180, 350),
            "肉類": (90, 200),
            "魚貝類": (90, 200),
            "蛋類": (50, 120),
            "豆類": (100, 250),
            "蔬菜類": (120, 300),
            "菇類": (60, 200),
            "水果類": (120, 300),
            "乳品類": (200, 350),
            "飲料類": (300, 600),
            "油脂類": (5, 25),
            "堅果及種子類": (10, 35),
            "糕餅點心類": (60, 200),
            "調味料及香辛料類": (5, 25),
            "藻類": (10, 60),
            "糖類": (5, 25),
            "加工調理食品及其他類": (200, 450),
        },
        "fitness": {
            "穀物類": (120, 250),
            "澱粉類": (120, 250),
            "肉類": (140, 280),
            "魚貝類": (140, 280),
            "蛋類": (50, 150),
            "豆類": (150, 300),
            "蔬菜類": (150, 350),
            "菇類": (80, 250),
            "水果類": (100, 250),
            "乳品類": (200, 400),
            "飲料類": (300, 700),
            "油脂類": (5, 20),
            "堅果及種子類": (10, 30),
            "糕餅點心類": (50, 150),
            "調味料及香辛料類": (5, 20),
            "藻類": (10, 60),
            "糖類": (5, 20),
            "加工調理食品及其他類": (180, 400),
        },
    }

    if profile not in ranges_by_profile:
        profile = "bento"

    ranges = ranges_by_profile[profile]
    default_min, default_max = (100, 250) if profile == "bento" else (120, 280)
    min_g, max_g = ranges.get(category or "", (default_min, default_max))
    mid_g = round((min_g + max_g) / 2, 1)
    return float(min_g), float(max_g), float(mid_g), "mid"


@router.get("/align", response_model=FoodAlignResponse)
async def align_food(
    q: str = Query(..., min_length=1, description="食物名稱或描述"),
    limit: int = Query(5, ge=1, le=20, description="回傳筆數上限")
):
    try:
        service = get_food_alignment_service()
        results = service.align(q, limit=limit)
        return FoodAlignResponse(
            query=q,
            count=len(results),
            results=[FoodMatch(**r) for r in results]
        )
    except Exception as e:
        logger.error(f"對齊失敗: {e}")
        raise HTTPException(status_code=500, detail=f"對齊失敗: {str(e)}")


@router.post("/llm/parse", response_model=FoodLLMParseResponse)
async def parse_llm_output(payload: FoodLLMParseRequest):
    try:
        raw = _extract_first_json(payload.raw_response)
        parsed = FoodVisionResult(**raw)

        db_match = None
        if parsed.food_candidates:
            top_name = parsed.food_candidates[0].name
            service = get_food_alignment_service()
            matches = service.align(top_name, limit=1)
            if matches:
                matched = matches[0]
                nutrients = service.get_food_nutrients(matched["food_id"])
                if nutrients:
                    db_match = FoodDBMatch(
                        food_id=nutrients["food_id"],
                        name=nutrients["name"],
                        category=nutrients["category"],
                        per_100g=nutrients["per_100g"],
                    )

        return FoodLLMParseResponse(parsed=parsed, db_match=db_match)
    except Exception as e:
        logger.error(f"LLM 解析失敗: {e}")
        raise HTTPException(status_code=400, detail=f"LLM 解析失敗: {str(e)}")


@router.post("/vision/suggest", response_model=FoodVisionSuggestResponse)
async def suggest_food_from_photo(
    file: UploadFile = File(...),
    limit: int = 5,
    profile: str = Query("bento", description="portion preset: bento|fitness"),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="僅支援圖片格式上傳")

    file_id = str(uuid4())
    file_ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, f"food_vision_{file_id}{file_ext}")

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        vision = food_vision_service.suggest_from_image(save_path, limit=limit)
        service = get_food_alignment_service()

        items: list[FoodVisionSuggestItem] = []
        for candidate in vision.food_candidates[:limit]:
            matched_food_id = None
            matched_name = None
            matched_category = None
            notes = None

            try:
                matches = service.align(candidate.name, limit=1)
                if matches:
                    top = matches[0]
                    matched_food_id = top["food_id"]
                    matched_name = top["name"]
                    matched_category = top["category"]
            except Exception as align_err:
                notes = f"align_failed: {align_err}"

            grams_min, grams_max, grams_mid, label = _estimate_grams_by_category(matched_category, profile=profile)
            items.append(FoodVisionSuggestItem(
                name=candidate.name,
                confidence=candidate.confidence,
                matched_food_id=matched_food_id,
                matched_name=matched_name,
                matched_category=matched_category,
                estimated_grams=grams_mid,
                grams_min=grams_min,
                grams_max=grams_max,
                estimate_label=label,
                notes=notes,
            ))

        return FoodVisionSuggestResponse(items=items, vision=vision)
    except Exception as e:
        logger.error(f"Photo suggest failed: {e}")
        raise HTTPException(status_code=500, detail=f"照片分析失敗: {str(e)}")
    finally:
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception:
            pass
