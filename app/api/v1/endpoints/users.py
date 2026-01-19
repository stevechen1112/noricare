from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple

from app.api import deps
from app.models.all_models import User, HealthRecord, AuthAccount
from app.schemas.user import (
    UserProfile,
    UserProfileCreate,
    UserHistoryResponse,
    HealthRecordHistoryItem,
    UserDashboardResponse,
    DashboardKeyMetric,
    DashboardAbnormalItem,
)
from app.schemas.analysis import NutritionReport
from app.services.nutrition_calculator import NutritionTargets, get_nutrition_targets_from_user

router = APIRouter()

@router.get("/me/profile", response_model=UserProfile)
def get_my_profile(
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    if not account.user_id:
        # 未建立 Profile 時回傳空白預設值
        return UserProfile(
            id=account.id, name="", age=0, gender="male", height_cm=0.0, weight_kg=0.0,
            health_goals=[], lifestyle={}, bmi=0.0
        )
    
    user = db.query(User).filter(User.id == account.user_id).first()
    if not user:
        return UserProfile(
            id=account.id, name="", age=0, gender="male", height_cm=0.0, weight_kg=0.0,
            health_goals=[], lifestyle={}, bmi=0.0
        )
        
    bmi = user.weight_kg / ((user.height_cm / 100) ** 2) if user.height_cm > 0 else 0.0
    return UserProfile(
            id=user.id, name=user.name, age=user.age, gender=user.gender,
            height_cm=user.height_cm, weight_kg=user.weight_kg,
            health_goals=user.health_goals, lifestyle=user.lifestyle_data,
            bmi=bmi
        )

@router.get("/me/nutrition-targets", response_model=NutritionTargets)
async def get_my_nutrition_targets(
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    # 憑使用者資料計算營養目標
    if not account.user_id:
        return NutritionTargets(calories=2000, protein=100, carbs=250, fat=65, fiber=25)
    
    user = db.query(User).filter(User.id == account.user_id).first()
    if not user or not all([user.weight_kg, user.height_cm, user.age, user.gender]):
        return NutritionTargets(calories=2000, protein=100, carbs=250, fat=65, fiber=25)
    
    return get_nutrition_targets_from_user(user)

@router.get("/me/dashboard", response_model=UserDashboardResponse)
def get_my_dashboard(
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    # 如果未建立 Profile 回傳 400 錯誤
    if not account.user_id:
        return UserDashboardResponse(
            user_id="guest", latest_record_date=None, health_score=None,
            key_metrics=[], abnormal_items=[], history=[], ai_report=None
        )

    user = db.query(User).filter(User.id == account.user_id).first()
    if not user:
        return UserDashboardResponse(
            user_id=account.id, latest_record_date=None, health_score=None,
            key_metrics=[], abnormal_items=[], history=[], ai_report=None
        )

    # ... 後續複雜邏輯暫時注釋 ...
    # 預計整合 AI 分析 API 相關功能
    return UserDashboardResponse(
        user_id=user.id, latest_record_date=None, health_score=None,
        key_metrics=[], abnormal_items=[], history=[], ai_report=None
    )

@router.post("/", response_model=UserProfile)
def create_user(
    user_in: UserProfileCreate,
    account: Optional[AuthAccount] = Depends(deps.get_current_account_optional),
    db: Session = Depends(deps.get_db),
):
    existing_user = db.query(User).filter(User.name == user_in.name).first()
    if existing_user:
        existing_user.age = user_in.age
        existing_user.weight_kg = user_in.weight_kg
        existing_user.height_cm = user_in.height_cm
        existing_user.health_goals = user_in.health_goals
        if user_in.lifestyle:


def _parse_reference_range(reference_range: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    if not reference_range:
        return None, None
    ref = reference_range.strip().replace(" ", "")
    try:
        if ref.startswith("<"):
            return None, float(ref[1:])
        if ref.startswith(">"):
            return float(ref[1:]), None
        if "-" in ref:
            parts = ref.split("-")
            if len(parts) == 2:
                return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None
    return None, None


def _infer_severity(value: float, min_val: Optional[float], max_val: Optional[float]) -> str:
    if min_val is None and max_val is None:
        return "warning"
    if max_val is not None and value > max_val:
        if value >= max_val * 1.2:
            return "danger"
        return "warning"
    if min_val is not None and value < min_val:
        if min_val > 0 and value <= min_val * 0.8:
            return "danger"
        return "warning"
    if max_val is not None and value >= max_val * 0.9:
        return "caution"
    if min_val is not None and value <= min_val * 1.1:
        return "caution"
    return "normal"


def _normalize_status(raw_status: Optional[str]) -> Optional[str]:
    if not raw_status:
        return None
    status = raw_status.lower()
    if status in {"high", "low", "warning", "fail"}:
        return "warning"
    if status in {"normal", "pass", "ok"}:
        return "normal"
    return None


def _extract_metric(clinical_data: Dict[str, Any], keys: List[str]) -> Optional[Dict[str, Any]]:
    for key in keys:
        for data_key, data_val in clinical_data.items():
            if key.lower() in str(data_key).lower():
                if isinstance(data_val, dict):
                    return {
                        "name": data_key,
                        "value": data_val.get("value"),
                        "unit": data_val.get("unit"),
                        "reference_range": data_val.get("reference_range"),
                        "status": data_val.get("status"),
                    }
                return {"name": data_key, "value": data_val}
    return None


def _build_key_metrics(user: User, clinical_data: Dict[str, Any]) -> List[DashboardKeyMetric]:
    metrics_def = [
        ("血糖", ["Glucose", "GLUCOSE", "血糖", "AC Sugar", "Fasting Glucose"], "mg/dL"),
        ("HbA1c", ["HbA1c", "HBA1C", "糖化血色素"], "%"),
        ("BMI", ["BMI"], ""),
        ("總膽固醇", ["TC", "Cholesterol", "總膽固醇"], "mg/dL"),
        ("三酸甘油酯", ["TG", "Triglyceride", "三酸甘油酯"], "mg/dL"),
        ("LDL", ["LDL", "低密度"], "mg/dL"),
        ("HDL", ["HDL", "高密度"], "mg/dL"),
    ]

    results: List[DashboardKeyMetric] = []

    for label, keys, default_unit in metrics_def:
        metric = _extract_metric(clinical_data, keys)
        if metric is None and label == "BMI":
            if user.height_cm and user.weight_kg:
                bmi = round(user.weight_kg / ((user.height_cm / 100) ** 2), 1)
                results.append(DashboardKeyMetric(label=label, value=bmi, unit=default_unit, status="normal"))
            continue

        if metric is None:
            continue

        value = metric.get("value")
        if value is None:
            continue

        try:
            value_num = float(value)
        except (TypeError, ValueError):
            value_num = None

        unit = metric.get("unit") or default_unit
        status = _normalize_status(metric.get("status"))
        min_val, max_val = _parse_reference_range(metric.get("reference_range"))

        if status is None and value_num is not None:
            status = _infer_severity(value_num, min_val, max_val)

        results.append(DashboardKeyMetric(
            label=label,
            value=value_num if value_num is not None else value,
            unit=unit,
            status=status or "normal",
        ))

        if len(results) >= 4:
            break

    return results


def _build_abnormal_items(clinical_data: Dict[str, Any]) -> List[DashboardAbnormalItem]:
    abnormal_items: List[DashboardAbnormalItem] = []

    for field_name, field_data in clinical_data.items():
        if not isinstance(field_data, dict):
            continue
        value = field_data.get("value")
        if value is None:
            continue

        try:
            value_num = float(value)
        except (TypeError, ValueError):
            continue

        reference_range = field_data.get("reference_range")
        min_val, max_val = _parse_reference_range(reference_range)
        status = _normalize_status(field_data.get("status"))

        if status == "normal":
            continue

        if status is None:
            severity = _infer_severity(value_num, min_val, max_val)
        else:
            severity = "warning"

        if severity == "normal":
            continue

        abnormal_items.append(DashboardAbnormalItem(
            name=str(field_name),
            value=value_num,
            unit=field_data.get("unit"),
            severity=severity,
            normal_range=reference_range,
        ))

    return abnormal_items

@router.post("/", response_model=UserProfile)
def create_user(
    user_in: UserProfileCreate,
    account: Optional[AuthAccount] = Depends(deps.get_current_account_optional),
    db: Session = Depends(deps.get_db),
):
    """
    建立或獲取現有使用者 (Get-or-Create)
    """
    # 1. Check if user exists by name (MVP Logic)
    existing_user = db.query(User).filter(User.name == user_in.name).first()
    
    if existing_user:
        # Update existing user profile
        existing_user.age = user_in.age
        existing_user.weight_kg = user_in.weight_kg
        existing_user.height_cm = user_in.height_cm
        existing_user.health_goals = user_in.health_goals
        if user_in.lifestyle:
            existing_user.lifestyle_data = user_in.lifestyle.dict()
            
        db.commit()
        db.refresh(existing_user)
        user = existing_user
    else:
        # Create new
        user = User(
            name=user_in.name,
            age=user_in.age,
            gender=user_in.gender,
            height_cm=user_in.height_cm,
            weight_kg=user_in.weight_kg,
            health_goals=user_in.health_goals,
            lifestyle_data=user_in.lifestyle.dict() if user_in.lifestyle else {},
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 綁定登入帳號的 user_id（避免 dashboard / meals 取不到資料）
    if account and account.user_id != user.id:
        account.user_id = user.id
        db.commit()

    # 簡單計算 BMI 用於存入
    bmi = user.weight_kg / ((user.height_cm / 100) ** 2)
    
    # 為了符合 response model (UserProfile 需要 id 和 bmi)
    user_resp = UserProfile(
        id=user.id,
        name=user.name,
        age=user.age,
        gender=user.gender,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        health_goals=user.health_goals,
        lifestyle=user.lifestyle_data, # 需轉換
        bmi=bmi
    )
    return user_resp

@router.get("/{user_id}/history", response_model=UserHistoryResponse)
def get_user_history(user_id: str, db: Session = Depends(deps.get_db)):
    """
    獲取使用者歷史健康紀錄 (用於趨勢圖表)
    """
    records = db.query(HealthRecord).filter(HealthRecord.user_id == user_id).order_by(HealthRecord.created_at.asc()).all()
    
    history_items = []
    for r in records:
        # Extract key metrics for charting
        metrics = {}
        if r.clinical_data:
            # 嘗試提取常見指標, 處理不同可能的 key 大小寫或格式
            targets = ["HbA1c", "GLUCOSE", "Glucose_PC", "eGFR", "BMI", "Cholesterol", "TG"]
            for t in targets:
                # 簡單模糊搜尋 key
                for k, v in r.clinical_data.items():
                    if t.lower() in k.lower():
                        # v is {"value": 117, "unit": ...}
                        val = v.get("value")
                        if isinstance(val, (int, float)):
                            metrics[t] = val
                            
        history_items.append(HealthRecordHistoryItem(
            record_id=r.id,
            created_at=r.created_at.strftime("%Y-%m-%d"),
            health_score=r.health_score,
            key_metrics=metrics
        ))
        
    return UserHistoryResponse(user_id=user_id, history=history_items)


@router.get("/{user_id}/records/latest", response_model=NutritionReport)
def get_latest_user_record(user_id: str, db: Session = Depends(deps.get_db)):
    """取得使用者最新一筆完整 AI 報告（用於 Flutter 端顯示/除錯）。"""
    record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .order_by(HealthRecord.created_at.desc())
        .first()
    )
    if not record or not record.ai_analysis:
        raise HTTPException(status_code=404, detail="No report found")

    data = dict(record.ai_analysis)
    data["report_id"] = record.id
    return NutritionReport(**data)


@router.get("/{user_id}/records/{record_id}", response_model=NutritionReport)
def get_user_record(user_id: str, record_id: str, db: Session = Depends(deps.get_db)):
    """取得使用者指定 record_id 的完整 AI 報告。"""
    record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id, HealthRecord.id == record_id)
        .first()
    )
    if not record or not record.ai_analysis:
        raise HTTPException(status_code=404, detail="Report not found")

    data = dict(record.ai_analysis)
    data["report_id"] = record.id
    return NutritionReport(**data)

@router.get("/", response_model=List[UserProfile])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    """
    獲取使用者列表
    """
    users = db.query(User).offset(skip).limit(limit).all()
    results = []
    for u in users:
        bmi = u.weight_kg / ((u.height_cm / 100) ** 2)
        results.append(UserProfile(
            id=u.id,
            name=u.name,
            age=u.age,
            gender=u.gender,
            height_cm=u.height_cm,
            weight_kg=u.weight_kg,
            health_goals=u.health_goals,
            lifestyle=u.lifestyle_data,
            bmi=bmi
        ))
    return results


# ============================================================
# 營養目標 API (方案 B - TDEE 計算)
# 注意：這些路由必須在 /{user_id} 之前，否則會被攔截
# ============================================================

@router.get("/me/nutrition-targets", response_model=NutritionTargets)
async def get_my_nutrition_targets(
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    """
    取得當前用戶的每日營養目標
    
    根據用戶的:
    - 身高、體重、年齡、性別
    - 活動量等級
    - 健康目標
    
    計算出每日建議攝取的:
    - 熱量 (kcal)
    - 蛋白質 (g)
    - 碳水化合物 (g)
    - 脂肪 (g)
    - 纖維 (g)
    """
    # 取得用戶的健康檔案
    if not account.user_id:
        raise HTTPException(
            status_code=400, 
            detail="請先完成健康檔案設定 (Profile)"
        )
    
    user = db.query(User).filter(User.id == account.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # 驗證必要欄位
    if not all([user.weight_kg, user.height_cm, user.age, user.gender]):
        raise HTTPException(
            status_code=400,
            detail="請完善個人資料 (身高、體重、年齡、性別)"
        )
    
    return get_nutrition_targets_from_user(user)


@router.get("/me/dashboard", response_model=UserDashboardResponse)
def get_my_dashboard(
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    if not account.user_id:
        raise HTTPException(status_code=400, detail="請先完成健康檔案設定 (Profile)")

    user = db.query(User).filter(User.id == account.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    latest_record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user.id)
        .order_by(HealthRecord.created_at.desc())
        .first()
    )

    clinical_data = latest_record.clinical_data if latest_record and latest_record.clinical_data else {}

    key_metrics = _build_key_metrics(user, clinical_data)
    abnormal_items = _build_abnormal_items(clinical_data)

    # history (reuse current logic for chart data)
    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user.id)
        .order_by(HealthRecord.created_at.asc())
        .all()
    )
    history_items: List[HealthRecordHistoryItem] = []
    for r in records:
        metrics = {}
        if r.clinical_data:
            targets = ["HbA1c", "GLUCOSE", "Glucose_PC", "eGFR", "BMI", "Cholesterol", "TG"]
            for t in targets:
                for k, v in r.clinical_data.items():
                    if t.lower() in str(k).lower():
                        val = v.get("value") if isinstance(v, dict) else None
                        if isinstance(val, (int, float)):
                            metrics[t] = val
        history_items.append(HealthRecordHistoryItem(
            record_id=r.id,
            created_at=r.created_at.strftime("%Y-%m-%d"),
            health_score=r.health_score,
            key_metrics=metrics,
        ))

    return UserDashboardResponse(
        user_id=user.id,
        latest_record_date=latest_record.created_at.strftime("%Y-%m-%d") if latest_record else None,
        health_score=latest_record.health_score if latest_record else None,
        key_metrics=key_metrics,
        abnormal_items=abnormal_items,
        history=history_items,
        ai_report=latest_record.ai_analysis if latest_record else None,
    )


# ============================================================
# 以下是需要 {user_id} 參數的路由
# ============================================================

@router.get("/{user_id}", response_model=UserProfile)
def read_user(user_id: str, db: Session = Depends(deps.get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    bmi = user.weight_kg / ((user.height_cm / 100) ** 2)
    return UserProfile(
            id=user.id,
            name=user.name,
            age=user.age,
            gender=user.gender,
            height_cm=user.height_cm,
            weight_kg=user.weight_kg,
            health_goals=user.health_goals,
            lifestyle=user.lifestyle_data,
            bmi=bmi
        )


@router.get("/{user_id}/nutrition-targets", response_model=NutritionTargets)
def get_user_nutrition_targets(
    user_id: str,
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db),
):
    """
    取得指定用戶的每日營養目標 (管理員或測試用)
    """
    if not account.user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if account.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not all([user.weight_kg, user.height_cm, user.age, user.gender]):
        raise HTTPException(
            status_code=400,
            detail="User profile incomplete"
        )
    
    return get_nutrition_targets_from_user(user)
