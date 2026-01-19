from typing import Dict, Any, Optional
from app.services.health_calculator import health_calculator

class HealthAnalyzer:
    """
    分析原始數據並生成 Health Snapshot (Sprint 2-3)
    """
    
    def analyze_snapshot(self, ocr_data: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合 OCR 與 User Profile，計算派生指標與風險標記
        """
        fields = ocr_data.get("fields", {})
        results = {
            "original_metrics": fields,
            "calculated_metrics": {},
            "risk_flags": [],
            "status": "success"
        }

        # 1. 處理 eGFR
        creatinine = self._get_numeric_value(fields, ["Creatinine", "肌酸酐", "CREA"])
        age = user_profile.get("age")
        is_male = user_profile.get("gender") == "male"

        if creatinine and age is not None:
            egfr_val = health_calculator.calculate_egfr(creatinine, age, is_male)
            results["calculated_metrics"]["eGFR"] = {
                "value": egfr_val,
                "unit": "ml/min/1.73m2",
                "stage": health_calculator.get_egfr_stage(egfr_val)
            }
            
            # eGFR 安全守門 (Safety Gate)
            if egfr_val < 60:
                results["risk_flags"].append({
                    "type": "medical_safety",
                    "item": "eGFR",
                    "level": "high",
                    "message": "腎功能指標低於 60，建議諮詢醫師並限制高鉀/高磷飲食。"
                })

        # 2. 處理血糖 (Glucose)
        glucose = self._get_numeric_value(fields, ["Glucose", "糖", "血糖", "GLU"])
        if glucose:
            if glucose >= 126:
                results["risk_flags"].append({
                    "type": "abnormal_value",
                    "item": "Glucose",
                    "level": "high",
                    "message": "空腹血糖偏高（≥126），具糖尿病風險。"
                })
            elif 100 <= glucose < 126:
                results["risk_flags"].append({
                    "type": "abnormal_value",
                    "item": "Glucose",
                    "level": "medium",
                    "message": "空腹血糖處於糖尿病前期偏高範圍。"
                })

        return results

    def _get_numeric_value(self, fields: Dict[str, Any], keys: list) -> Optional[float]:
        """
        從 OCR 欄位中尋找匹配的數值
        """
        for key in keys:
            if key in fields:
                val = fields[key].get("value")
                try:
                    return float(val) if val is not None else None
                except ValueError:
                    continue
        return None

health_analyzer = HealthAnalyzer()
