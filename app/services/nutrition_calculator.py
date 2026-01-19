"""
TDEE 與營養目標計算服務

此服務根據用戶的身體數據計算：
1. BMR (基礎代謝率) - 使用 Mifflin-St Jeor 公式
2. TDEE (每日總能量消耗) - BMR × 活動量乘數
3. 三大營養素目標 - 蛋白質、碳水化合物、脂肪
"""

from typing import Optional, Literal
from pydantic import BaseModel

# 活動量乘數 (基於 TDEE 標準)
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,      # 久坐 (幾乎不運動)
    "light": 1.375,        # 輕度活動 (每週 1-3 天運動)
    "moderate": 1.55,      # 中度活動 (每週 3-5 天運動)
    "active": 1.725,       # 高度活動 (每週 6-7 天運動)
    "very_active": 1.9,    # 非常活躍 (每天高強度運動或體力工作)
}

# 健康目標調整係數
GOAL_ADJUSTMENTS = {
    "減重": -0.15,         # 減少 15% 熱量
    "減脂": -0.15,
    "瘦身": -0.15,
    "增肌": 0.10,          # 增加 10% 熱量
    "增重": 0.15,          # 增加 15% 熱量
    "維持體重": 0.0,
    "控糖": 0.0,           # 控糖不影響總熱量，影響營養素比例
    "降膽固醇": 0.0,
    "改善睡眠": 0.0,
}


class NutritionTargets(BaseModel):
    """每日營養目標"""
    calories: int           # 每日熱量目標 (kcal)
    protein_g: int          # 蛋白質目標 (g)
    carbs_g: int            # 碳水化合物目標 (g)
    fat_g: int              # 脂肪目標 (g)
    fiber_g: int            # 纖維目標 (g)
    
    # 計算依據（便於前端顯示）
    bmr: int                # 基礎代謝率
    tdee: int               # 每日總能量消耗
    activity_level: str     # 活動量等級
    goal_adjustment: float  # 目標調整百分比
    
    # 營養素熱量佔比（便於圖表顯示）
    protein_ratio: float    # 蛋白質熱量佔比 (0-1)
    carbs_ratio: float      # 碳水熱量佔比 (0-1)
    fat_ratio: float        # 脂肪熱量佔比 (0-1)


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: Literal["male", "female", "other"]
) -> float:
    """
    計算基礎代謝率 (BMR) - 使用 Mifflin-St Jeor 公式
    
    這個公式被認為是目前最準確的 BMR 計算方法
    
    男性: BMR = (10 × 體重kg) + (6.25 × 身高cm) - (5 × 年齡) + 5
    女性: BMR = (10 × 體重kg) + (6.25 × 身高cm) - (5 × 年齡) - 161
    """
    if gender == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        # 女性和其他性別使用女性公式
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    
    return bmr


def calculate_tdee(
    bmr: float,
    activity_level: str
) -> float:
    """
    計算每日總能量消耗 (TDEE)
    
    TDEE = BMR × 活動量乘數
    """
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return bmr * multiplier


def determine_goal_adjustment(health_goals: list[str]) -> float:
    """
    根據健康目標決定熱量調整
    
    如果有多個目標，取最顯著的調整（減重優先於增肌）
    """
    adjustment = 0.0
    
    for goal in health_goals:
        if goal in GOAL_ADJUSTMENTS:
            goal_adj = GOAL_ADJUSTMENTS[goal]
            # 如果是減重類目標，優先採用
            if goal_adj < 0:
                adjustment = min(adjustment, goal_adj)
            elif adjustment >= 0:
                adjustment = max(adjustment, goal_adj)
    
    return adjustment


def calculate_macros(
    target_calories: int,
    weight_kg: float,
    health_goals: list[str]
) -> dict:
    """
    計算三大營養素目標
    
    標準比例：
    - 蛋白質: 1.6g/kg 體重 (運動者可達 2.0g/kg)
    - 脂肪: 總熱量的 25-30%
    - 碳水化合物: 剩餘熱量
    
    控糖模式：
    - 碳水降低到 40%
    - 脂肪和蛋白質相應增加
    """
    # 判斷是否需要特殊比例
    is_low_carb = any(g in ["控糖", "生酮", "低碳"] for g in health_goals)
    is_muscle_gain = any(g in ["增肌"] for g in health_goals)
    
    # 計算蛋白質 (基於體重)
    protein_per_kg = 1.6
    if is_muscle_gain:
        protein_per_kg = 2.0
    protein_g = int(weight_kg * protein_per_kg)
    
    # 蛋白質熱量 (1g = 4 kcal)
    protein_calories = protein_g * 4
    
    # 計算脂肪
    if is_low_carb:
        fat_ratio = 0.35  # 控糖模式脂肪佔 35%
    else:
        fat_ratio = 0.28  # 標準模式脂肪佔 28%
    
    fat_calories = target_calories * fat_ratio
    fat_g = int(fat_calories / 9)  # 1g 脂肪 = 9 kcal
    
    # 剩餘熱量給碳水化合物
    carbs_calories = target_calories - protein_calories - fat_calories
    carbs_calories = max(0, carbs_calories)
    carbs_g = int(carbs_calories / 4)  # 1g 碳水 = 4 kcal
    
    # 確保碳水不會是負數
    if carbs_g < 50:
        carbs_g = 50
        # 重新調整脂肪
        remaining = target_calories - protein_calories - (carbs_g * 4)
        if remaining < 0:
            fat_g = 0
        else:
            fat_g = int(remaining / 9)
    
    # 計算實際比例
    total_macro_cal = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
    protein_ratio = (protein_g * 4) / total_macro_cal if total_macro_cal > 0 else 0.25
    carbs_ratio = (carbs_g * 4) / total_macro_cal if total_macro_cal > 0 else 0.45
    fat_ratio = (fat_g * 9) / total_macro_cal if total_macro_cal > 0 else 0.30
    
    return {
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "protein_ratio": round(protein_ratio, 2),
        "carbs_ratio": round(carbs_ratio, 2),
        "fat_ratio": round(fat_ratio, 2),
    }


def calculate_fiber(target_calories: int) -> int:
    """
    計算膳食纖維目標
    
    建議攝取量: 每 1000 kcal 攝取 14g 纖維
    最低: 25g, 最高: 38g
    """
    fiber = int((target_calories / 1000) * 14)
    return max(25, min(38, fiber))


def calculate_nutrition_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: Literal["male", "female", "other"],
    activity_level: str = "sedentary",
    health_goals: Optional[list[str]] = None
) -> NutritionTargets:
    """
    計算完整的每日營養目標
    
    主要計算步驟:
    1. 計算 BMR
    2. 計算 TDEE (BMR × 活動量)
    3. 根據健康目標調整熱量
    4. 計算三大營養素分配
    """
    if health_goals is None:
        health_goals = []
    
    # 1. 計算 BMR
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    
    # 2. 計算 TDEE
    tdee = calculate_tdee(bmr, activity_level)
    
    # 3. 根據目標調整
    goal_adjustment = determine_goal_adjustment(health_goals)
    target_calories = int(tdee * (1 + goal_adjustment))
    
    # 確保最低熱量 (避免過度節食)
    min_calories = 1200 if gender != "male" else 1500
    target_calories = max(min_calories, target_calories)
    
    # 4. 計算三大營養素
    macros = calculate_macros(target_calories, weight_kg, health_goals)
    
    # 5. 計算纖維
    fiber_g = calculate_fiber(target_calories)
    
    return NutritionTargets(
        calories=target_calories,
        protein_g=macros["protein_g"],
        carbs_g=macros["carbs_g"],
        fat_g=macros["fat_g"],
        fiber_g=fiber_g,
        bmr=int(bmr),
        tdee=int(tdee),
        activity_level=activity_level,
        goal_adjustment=goal_adjustment,
        protein_ratio=macros["protein_ratio"],
        carbs_ratio=macros["carbs_ratio"],
        fat_ratio=macros["fat_ratio"],
    )


def get_nutrition_targets_from_user(user) -> NutritionTargets:
    """
    從 User model 取得營養目標
    
    這是 API 端點呼叫的主要入口
    """
    # 從 lifestyle_data 取得活動量
    lifestyle = user.lifestyle_data or {}
    activity_level = lifestyle.get("activity_level", "sedentary")
    
    # 健康目標
    health_goals = user.health_goals or []
    
    return calculate_nutrition_targets(
        weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        age=user.age,
        gender=user.gender,
        activity_level=activity_level,
        health_goals=health_goals,
    )
