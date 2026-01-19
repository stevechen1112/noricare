"""
Phase 1 營養資料庫驗證測試
==========================
驗證 Top 20 常見食物的匹配率是否達標 (≥80%)

成功指標：
- Top 20 常見食物匹配率 ≥ 80%
- 查詢響應時間 < 100ms
- API 健康運作

執行方式：
python test_nutrition_db.py
"""

import sys
import os
import time
import json

# 確保可以 import app 模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.nutrition_db_service import NutritionDBService


def main():
    print("=" * 60)
    print("Phase 1 營養資料庫驗證測試")
    print("=" * 60)
    
    # 初始化服務
    print("\n📦 載入營養資料庫...")
    start_time = time.time()
    service = NutritionDBService()
    
    # 測試載入
    stats = service.get_stats()
    load_time = (time.time() - start_time) * 1000
    print(f"   ✅ 載入完成: {stats['total_foods']} 筆食物, {stats['total_categories']} 個分類")
    print(f"   ⏱️  載入時間: {load_time:.1f}ms")
    
    # Top 20 驗證
    print("\n🔍 Top 20 常見食物匹配率驗證...")
    print("-" * 60)
    
    validation = service.validate_top20_foods()
    
    for item in validation['details']:
        status = "✅" if item['matched'] else "❌"
        matched_name = item['matched_name'] or "無匹配"
        print(f"   {status} {item['query']:8s} → {matched_name}")
    
    print("-" * 60)
    print(f"\n📊 驗證結果:")
    print(f"   測試數量: {validation['test_count']}")
    print(f"   匹配數量: {validation['matched_count']}")
    print(f"   匹配率: {validation['match_rate_percent']:.1f}%")
    print(f"   目標值: {validation['target_rate_percent']}%")
    
    if validation['passed']:
        print(f"\n🎉 通過！匹配率 {validation['match_rate_percent']:.1f}% ≥ 80%")
    else:
        print(f"\n⚠️  未通過：匹配率 {validation['match_rate_percent']:.1f}% < 80%")
        print("   需要擴充別名映射表")
    
    # 查詢效能測試
    print("\n⏱️  查詢效能測試...")
    test_queries = ['白飯', '雞胸肉', '蘋果', '豆腐', '菠菜']
    total_time = 0
    
    for query in test_queries:
        start = time.time()
        results = service.search(query)
        elapsed = (time.time() - start) * 1000
        total_time += elapsed
        print(f"   {query}: {len(results)} 筆結果, {elapsed:.2f}ms")
    
    avg_time = total_time / len(test_queries)
    print(f"\n   平均查詢時間: {avg_time:.2f}ms {'✅' if avg_time < 100 else '❌'}")
    
    # 營養計算測試
    print("\n🧮 營養計算測試...")
    test_meals = [
        ('白飯', 200),   # 一碗飯約 200g
        ('雞胸肉', 150), # 一份雞胸約 150g
        ('菠菜', 100),   # 一份蔬菜約 100g
    ]
    
    total_cal = 0
    total_protein = 0
    total_carbs = 0
    
    for food, grams in test_meals:
        result = service.calculate_nutrients(food, grams)
        if result:
            n = result['nutrients']
            total_cal += n['calories']
            total_protein += n['protein']
            total_carbs += n['carbs']
            print(f"   {food} {grams}g: {n['calories']:.0f} kcal, "
                  f"{n['protein']:.1f}g 蛋白質, {n['carbs']:.1f}g 碳水")
    
    print(f"\n   一餐總計: {total_cal:.0f} kcal, {total_protein:.1f}g 蛋白質, {total_carbs:.1f}g 碳水")
    
    # 最終報告
    print("\n" + "=" * 60)
    print("Phase 1 驗證報告")
    print("=" * 60)
    
    all_passed = True
    
    # 指標 1: 匹配率
    indicator1 = validation['passed']
    print(f"✓ 指標 1 - Top 20 匹配率: {validation['match_rate_percent']:.1f}% "
          f"{'✅ PASS' if indicator1 else '❌ FAIL'}")
    all_passed = all_passed and indicator1
    
    # 指標 2: 查詢效能
    indicator2 = avg_time < 100
    print(f"✓ 指標 2 - 查詢效能: {avg_time:.2f}ms "
          f"{'✅ PASS' if indicator2 else '❌ FAIL'}")
    all_passed = all_passed and indicator2
    
    # 指標 3: 資料完整性
    indicator3 = stats['total_foods'] >= 2000
    print(f"✓ 指標 3 - 資料完整性: {stats['total_foods']} 筆 "
          f"{'✅ PASS' if indicator3 else '❌ FAIL'}")
    all_passed = all_passed and indicator3
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 Phase 1 驗證全部通過！可以進入 Phase 2")
    else:
        print("⚠️  部分指標未通過，需要調整後重新驗證")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
