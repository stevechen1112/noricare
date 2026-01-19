from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Dict, List
from sqlalchemy.orm import Session
import math

from app.services.ai_service import ai_service
from app.schemas.user import UserProfile
from app.schemas.analysis import NutritionReport, HealthMetricStatus
from app.api import deps
from app.models.all_models import AuthAccount, HealthRecord, User

router = APIRouter()


def _merge_health_goals(existing: list[str], inferred: list[str]) -> list[str]:
    merged: list[str] = []
    seen = set()
    for goal in existing + inferred:
        if not goal:
            continue
        if goal not in seen:
            merged.append(goal)
            seen.add(goal)
    return merged


def _is_abnormal(status_value: str | None) -> bool:
    if not status_value:
        return False
    status = status_value.strip().lower()
    return status not in {"normal", "ok", "pass"}


def _infer_health_goals(health_data: dict, abnormal_items: list, user_profile: UserProfile) -> list[str]:
    goals: list[str] = []

    def add_goal(goal: str):
        if goal not in goals:
            goals.append(goal)

    # BMI-based goals
    if user_profile.height_cm and user_profile.weight_kg:
        bmi = user_profile.weight_kg / ((user_profile.height_cm / 100) ** 2)
        if bmi >= 24:
            add_goal("減重")
        elif bmi <= 18.5:
            add_goal("增重")

    # Abnormal items string hints
    abnormal_text = " ".join([str(item) for item in abnormal_items or []])
    if any(k in abnormal_text for k in ["血糖", "Glucose", "HbA1c", "糖化血色素"]):
        add_goal("控糖")
    if any(k in abnormal_text for k in ["膽固醇", "Cholesterol", "LDL", "TG", "三酸甘油酯", "Triglyceride"]):
        add_goal("降膽固醇")
        add_goal("減脂")

    # Structured health data with status
    for field_name, field_data in (health_data or {}).items():
        if not isinstance(field_data, dict):
            continue
        if not _is_abnormal(str(field_data.get("status")) if field_data.get("status") is not None else None):
            continue
        name = str(field_name)
        if any(k.lower() in name.lower() for k in ["glucose", "血糖", "hba1c", "糖化血色素"]):
            add_goal("控糖")
        if any(k.lower() in name.lower() for k in ["cholesterol", "膽固醇", "ldl", "tg", "triglyceride", "三酸甘油酯"]):
            add_goal("降膽固醇")
            add_goal("減脂")

    return goals

# 暫時定義一個請求結構
class RecommendationRequest(BaseModel):
    user_profile: UserProfile
    health_data: Dict[str, HealthMetricStatus]
    abnormal_items: List[str]


def calculate_egfr_ckd_epi(creatinine: float, age: int, is_male: bool) -> float:
    """CKD-EPI 2021 公式計算 eGFR"""
    kappa = 0.9 if is_male else 0.7
    alpha = -0.302 if is_male else -0.241
    scr_kappa = creatinine / kappa
    egfr = 142 * (min(scr_kappa, 1.0) ** alpha) * (max(scr_kappa, 1.0) ** -1.200) * (0.9938 ** age) * (1.0 if is_male else 1.012)
    return round(egfr, 1)


def calculate_health_score(health_data: dict, abnormal_items: list) -> int:
    """
    動態計算健康評分（滿分 100）
    - 基礎分數 100
    - 每個異常項目扣分
    """
    score = 100
    
    # 根據異常項目數量扣分
    for item in abnormal_items:
        item_lower = item.lower()
        # 嚴重異常扣較多分
        if '糖尿病' in item or 'diabetes' in item_lower:
            score -= 8
        elif 'hba1c' in item_lower or '糖化血色素' in item:
            score -= 6
        elif '血糖' in item or 'glucose' in item_lower:
            score -= 5
        elif 'egfr' in item_lower or '腎' in item:
            score -= 7
        elif 'bmi' in item_lower or '過重' in item or '肥胖' in item:
            score -= 4
        elif 'ldl' in item_lower or '膽固醇' in item:
            score -= 4
        elif 'ast' in item_lower or 'alt' in item_lower or '肝' in item:
            score -= 5
        else:
            score -= 3  # 一般異常
    
    return max(score, 30)  # 最低 30 分


def analyze_health_risks(health_data: dict, age: int, is_male: bool) -> dict:
    """
    完整健康風險評估（從 MVP 移植）
    """
    risk_assessment = {
        "心血管風險": [],
        "代謝風險": [],
        "肝功能風險": [],
        "腎功能風險": [],
        "calculated_metrics": {}
    }
    
    # 檢查所有可能的欄位名稱
    def get_value(keys: list) -> float:
        for k in keys:
            for data_key, data_val in health_data.items():
                if k.lower() in data_key.lower():
                    val = data_val.get('value') if isinstance(data_val, dict) else data_val
                    if val is not None:
                        try:
                            return float(val)
                        except:
                            pass
        return None
    
    # === 血糖風險 ===
    glucose = get_value(['GLUCOSE', 'Glucose', '血糖', 'AC Sugar', 'Fasting Glucose'])
    if glucose:
        if glucose >= 126:
            risk_assessment["代謝風險"].append(f"🔴 空腹血糖 {glucose} mg/dL - 已達糖尿病標準")
        elif glucose >= 100:
            risk_assessment["代謝風險"].append(f"🟡 空腹血糖 {glucose} mg/dL - 糖尿病前期")
    
    # 飯後血糖
    pc_glucose = get_value(['Post-prandial', 'Glucose_PC', '飯後血糖', 'PC Sugar'])
    if pc_glucose:
        if pc_glucose >= 200:
            risk_assessment["代謝風險"].append(f"🔴 飯後血糖 {pc_glucose} mg/dL - 糖尿病範圍")
        elif pc_glucose >= 140:
            risk_assessment["代謝風險"].append(f"🟡 飯後血糖 {pc_glucose} mg/dL - 葡萄糖耐受不良")
    
    # HbA1c
    hba1c = get_value(['HbA1c', 'HBA1C', '糖化血色素'])
    if hba1c:
        if hba1c >= 6.5:
            risk_assessment["代謝風險"].append(f"🔴 HbA1c {hba1c}% - 糖尿病範圍")
        elif hba1c >= 5.7:
            risk_assessment["代謝風險"].append(f"🟡 HbA1c {hba1c}% - 糖尿病前期")
    
    # === 腎功能 ===
    creatinine = get_value(['Creatinine', 'CREA', '肌酸酐', 'Cr', 'CRE'])
    if creatinine:
        # 計算 eGFR
        egfr = calculate_egfr_ckd_epi(creatinine, age, is_male)
        risk_assessment["calculated_metrics"]["eGFR_calculated"] = egfr
        
        if egfr >= 90:
            risk_assessment["calculated_metrics"]["腎功能分期"] = "G1 - 正常"
        elif egfr >= 60:
            risk_assessment["calculated_metrics"]["腎功能分期"] = "G2 - 輕度下降"
        elif egfr >= 45:
            risk_assessment["腎功能風險"].append(f"🟡 eGFR {egfr} - G3a 中度下降")
            risk_assessment["calculated_metrics"]["腎功能分期"] = "G3a - 中度下降"
        elif egfr >= 30:
            risk_assessment["腎功能風險"].append(f"🔴 eGFR {egfr} - G3b 中重度下降")
            risk_assessment["calculated_metrics"]["腎功能分期"] = "G3b - 中重度下降"
        else:
            risk_assessment["腎功能風險"].append(f"🔴 eGFR {egfr} - 嚴重腎功能不全")
            risk_assessment["calculated_metrics"]["腎功能分期"] = "G4/G5 - 嚴重"
    
    # === 血脂 ===
    ldl = get_value(['LDL', '低密度'])
    if ldl and ldl > 130:
        risk_assessment["心血管風險"].append(f"🟡 LDL {ldl} mg/dL 偏高")
    
    tc = get_value(['TC', 'Cholesterol', '總膽固醇'])
    if tc and tc > 200:
        risk_assessment["心血管風險"].append(f"🟡 總膽固醇 {tc} mg/dL 偏高")
    
    tg = get_value(['TG', 'Triglyceride', '三酸甘油酯'])
    if tg and tg > 150:
        risk_assessment["心血管風險"].append(f"🟡 三酸甘油酯 {tg} mg/dL 偏高")
    
    hdl = get_value(['HDL', '高密度'])
    if hdl and hdl < 40:
        risk_assessment["心血管風險"].append(f"🟡 HDL {hdl} mg/dL 偏低 (保護因子不足)")
    
    # === 肝功能 ===
    ast = get_value(['AST', 'GOT'])
    if ast and ast > 40:
        risk_assessment["肝功能風險"].append(f"🟡 AST/GOT {ast} U/L 偏高")
    
    alt = get_value(['ALT', 'GPT'])
    if alt and alt > 40:
        risk_assessment["肝功能風險"].append(f"🟡 ALT/GPT {alt} U/L 偏高")
    
    # 清理空的風險類別
    risk_assessment = {k: v for k, v in risk_assessment.items() if v}
    
    return risk_assessment


@router.post("/generate", response_model=NutritionReport)
async def generate_recommendation(
    request: RecommendationRequest,
    account: AuthAccount = Depends(deps.get_current_account),
    db: Session = Depends(deps.get_db)
):
    """
    生成完整的營養與健康建議報告，並存入資料庫。
    """
    
    # 1. 轉換數據
    health_data_dict = {k: v.dict() for k, v in request.health_data.items()}
    
    # 1.5 進行完整健康風險評估（從 MVP 移植的核心邏輯）
    is_male = request.user_profile.gender == "male"
    age = request.user_profile.age or 40
    
    risk_assessment = analyze_health_risks(health_data_dict, age, is_male)
    
    # 動態計算健康評分
    health_score = calculate_health_score(health_data_dict, request.abnormal_items)
    
    # 不要把 risk_assessment 加入 health_data_dict（會破壞 schema）
    # 改為單獨傳給 AI Service
    
    # print(f"[Recommendation] Risk Assessment: {risk_assessment}")
    # print(f"[Recommendation] Health Score: {health_score}")
    # print(f"[Recommendation] Abnormal Items: {request.abnormal_items}")
    
    # 2. 獲取歷史數據 (Trend Analysis)
    history_records = []
    user_id = account.user_id or request.user_profile.id
    if user_id:
        # 查詢最近的 1 筆記錄 (不包含剛才可能重複操作的)
        last_record = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id
        ).order_by(HealthRecord.created_at.desc()).first()
        
        if last_record:
             # 簡單處理，只取 clinical_data
             history_records.append({
                 "date": last_record.created_at.strftime("%Y-%m-%d"),
                 "data": last_record.clinical_data
             })
    
    try:
        # 3. AI 生成 (带入历史 + 風險評估)
        report = await ai_service.generate_comprehensive_report(
            user_profile=request.user_profile,
            health_data=health_data_dict,
            abnormal_items=request.abnormal_items,
            history_records=history_records,
            risk_assessment=risk_assessment  # 新增：傳入風險評估
        )
        
        # 覆寫健康評分為動態計算的分數
        report.health_score = health_score
        
        # 4. 存入資料庫 (Persistence)
        # 為了 MVP 簡單，我們假設 user_profile.id 是有效的 user_id
        # 如果 user_id 是 "temp"，可能需要處理
        
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                inferred_goals = _infer_health_goals(
                    health_data_dict,
                    request.abnormal_items,
                    request.user_profile,
                )
                if inferred_goals:
                    merged_goals = _merge_health_goals(user.health_goals or [], inferred_goals)
                    if merged_goals != (user.health_goals or []):
                        user.health_goals = merged_goals
                        db.commit()

            record = HealthRecord(
                user_id=user_id,
                clinical_data=health_data_dict,
                ai_analysis=report.dict(), # 儲存完整報告結構
                abnormal_items=request.abnormal_items,
                health_score=health_score  # 使用動態計算的分數
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            
            # 更新 report_id
            report.report_id = record.id
            # 同步更新資料庫內的 ai_analysis（避免 DB 與回傳內容不一致）
            record.ai_analysis = report.dict()
            db.commit()
            
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")

