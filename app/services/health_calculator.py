import math
from typing import Optional

class HealthCalculator:
    """
    提供各項健康指標的計算服務 (Sprint 2)
    包含 eGFR, BMI, 理想體重等。
    """

    @staticmethod
    def calculate_egfr(creatinine: float, age: int, is_male: bool) -> float:
        """
        使用 CKD-EPI (2021) 公式計算 eGFR (不分種族版本)
        適用於成人。
        :param creatinine: 血清肌酸酐 (mg/dL)
        :param age: 年齡
        :param is_male: 是否為男性
        :return: eGFR (ml/min/1.73m2)
        """
        # CKD-EPI 2021 常數
        kappa = 0.9 if is_male else 0.7
        alpha = -0.302 if is_male else -0.241
        constant = 142
        gender_multiplier = 1.0 if is_male else 1.012

        scr_kappa = creatinine / kappa
        
        egfr = constant * \
               math.pow(min(scr_kappa, 1.0), alpha) * \
               math.pow(max(scr_kappa, 1.0), -1.200) * \
               math.pow(0.9938, age) * \
               gender_multiplier
        
        return round(egfr, 1)

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> Optional[float]:
        """
        計算 BMI
        """
        if height_cm <= 0:
            return None
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        return round(bmi, 2)

    @staticmethod
    def get_egfr_stage(egfr: float) -> str:
        """
        根據 eGFR 判斷慢性腎臟病分期 (Taiwan CKD Standard)
        """
        if egfr >= 90:
            return "第一期：腎功能正常"
        elif 60 <= egfr < 90:
            return "第二期：腎功能輕度下降"
        elif 45 <= egfr < 60:
            return "第三期甲：腎功能中重度下降"
        elif 30 <= egfr < 45:
            return "第三期乙：腎功能中重度下降"
        elif 15 <= egfr < 30:
            return "第四期：腎功能顯著下降"
        else:
            return "第五期：末期腎臟病"

health_calculator = HealthCalculator()
