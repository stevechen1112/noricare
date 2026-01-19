import 'package:dio/dio.dart';
import 'api_client.dart';

/// 營養查詢服務 (Phase 1 MVP)
/// 獨立於現有 AI 報告流程，用於驗證資料庫整合價值
class NutritionService {
  final Dio _dio = ApiClient.instance.dio;

  // ============ 營養目標 API (方案 B) ============

  /// 取得當前用戶的每日營養目標
  /// 基於 TDEE 計算（身高、體重、年齡、活動量、健康目標）
  Future<NutritionTargets> getMyNutritionTargets() async {
    try {
      final response = await _dio.get('/users/me/nutrition-targets');
      return NutritionTargets.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// 取得今日飲食攝取統計
  Future<TodaySummary> getTodaySummary() async {
    try {
      final response = await _dio.get('/meals/summary/today');
      return TodaySummary.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// 取得今日營養進度（結合目標和實際攝取）
  Future<NutritionProgress> getTodayProgress() async {
    try {
      // 並行取得目標和今日統計
      final results = await Future.wait([
        getMyNutritionTargets(),
        getTodaySummary(),
      ]);
      
      final targets = results[0] as NutritionTargets;
      final today = results[1] as TodaySummary;
      
      return NutritionProgress(
        targets: targets,
        consumed: today.totalNutrients,
        meals: today.meals,
        date: today.date,
      );
    } catch (e) {
      rethrow;
    }
  }

  // ============ 原有 API ============

  /// 搜尋食物營養資訊
  Future<NutritionSearchResult> searchFood(String query, {int limit = 5}) async {
    try {
      final response = await _dio.get(
        '/nutrition/search',
        queryParameters: {
          'q': query,
          'limit': limit,
        },
      );
      return NutritionSearchResult.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// 計算指定克數的營養成分
  Future<CalculatedNutrients> calculateNutrients(String food, double grams) async {
    try {
      final response = await _dio.get(
        '/nutrition/calculate',
        queryParameters: {
          'food': food,
          'grams': grams,
        },
      );
      return CalculatedNutrients.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// 取得食品分類列表
  Future<List<String>> getCategories() async {
    try {
      final response = await _dio.get('/nutrition/categories');
      return List<String>.from(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// 取得服務統計
  Future<NutritionStats> getStats() async {
    try {
      final response = await _dio.get('/nutrition/stats');
      return NutritionStats.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException e) {
    if (e.response?.statusCode == 404) {
      return Exception('找不到該食物');
    }
    return Exception(e.message ?? '網路錯誤');
  }
}

// ============ 資料模型 ============

class NutrientsPer100g {
  final double calories;
  final double protein;
  final double carbs;
  final double fat;
  final double sodium;
  final double fiber;
  final double potassium;

  NutrientsPer100g({
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.sodium,
    required this.fiber,
    required this.potassium,
  });

  factory NutrientsPer100g.fromJson(Map<String, dynamic> json) {
    return NutrientsPer100g(
      calories: (json['calories'] ?? 0).toDouble(),
      protein: (json['protein'] ?? 0).toDouble(),
      carbs: (json['carbs'] ?? 0).toDouble(),
      fat: (json['fat'] ?? 0).toDouble(),
      sodium: (json['sodium'] ?? 0).toDouble(),
      fiber: (json['fiber'] ?? 0).toDouble(),
      potassium: (json['potassium'] ?? 0).toDouble(),
    );
  }
}

class FoodNutrition {
  final String name;
  final String category;
  final NutrientsPer100g per100g;

  FoodNutrition({
    required this.name,
    required this.category,
    required this.per100g,
  });

  factory FoodNutrition.fromJson(Map<String, dynamic> json) {
    return FoodNutrition(
      name: json['name'] ?? '',
      category: json['category'] ?? '',
      per100g: NutrientsPer100g.fromJson(json['per_100g'] ?? {}),
    );
  }
}

class NutritionSearchResult {
  final String query;
  final int count;
  final List<FoodNutrition> results;

  NutritionSearchResult({
    required this.query,
    required this.count,
    required this.results,
  });

  factory NutritionSearchResult.fromJson(Map<String, dynamic> json) {
    return NutritionSearchResult(
      query: json['query'] ?? '',
      count: json['count'] ?? 0,
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => FoodNutrition.fromJson(e))
              .toList() ??
          [],
    );
  }
}

class CalculatedNutrients {
  final String name;
  final double grams;
  final NutrientsPer100g nutrients;

  CalculatedNutrients({
    required this.name,
    required this.grams,
    required this.nutrients,
  });

  factory CalculatedNutrients.fromJson(Map<String, dynamic> json) {
    return CalculatedNutrients(
      name: json['name'] ?? '',
      grams: (json['grams'] ?? 0).toDouble(),
      nutrients: NutrientsPer100g.fromJson(json['nutrients'] ?? {}),
    );
  }
}

class NutritionStats {
  final int totalFoods;
  final int totalCategories;
  final double matchRatePercent;
  final String status;

  NutritionStats({
    required this.totalFoods,
    required this.totalCategories,
    required this.matchRatePercent,
    required this.status,
  });

  factory NutritionStats.fromJson(Map<String, dynamic> json) {
    return NutritionStats(
      totalFoods: json['total_foods'] ?? 0,
      totalCategories: json['total_categories'] ?? 0,
      matchRatePercent: (json['match_rate_percent'] ?? 0).toDouble(),
      status: json['status'] ?? 'unknown',
    );
  }
}

// ============ 方案 B: 營養目標相關模型 ============

/// 每日營養目標 (基於 TDEE 計算)
class NutritionTargets {
  final int calories;      // 每日熱量目標 (kcal)
  final int proteinG;      // 蛋白質目標 (g)
  final int carbsG;        // 碳水化合物目標 (g)
  final int fatG;          // 脂肪目標 (g)
  final int fiberG;        // 纖維目標 (g)
  
  // 計算依據
  final int bmr;           // 基礎代謝率
  final int tdee;          // 每日總能量消耗
  final String activityLevel;
  final double goalAdjustment;
  
  // 營養素熱量佔比
  final double proteinRatio;
  final double carbsRatio;
  final double fatRatio;

  NutritionTargets({
    required this.calories,
    required this.proteinG,
    required this.carbsG,
    required this.fatG,
    required this.fiberG,
    required this.bmr,
    required this.tdee,
    required this.activityLevel,
    required this.goalAdjustment,
    required this.proteinRatio,
    required this.carbsRatio,
    required this.fatRatio,
  });

  factory NutritionTargets.fromJson(Map<String, dynamic> json) {
    return NutritionTargets(
      calories: json['calories'] ?? 2000,
      proteinG: json['protein_g'] ?? 120,
      carbsG: json['carbs_g'] ?? 250,
      fatG: json['fat_g'] ?? 67,
      fiberG: json['fiber_g'] ?? 28,
      bmr: json['bmr'] ?? 1600,
      tdee: json['tdee'] ?? 2000,
      activityLevel: json['activity_level'] ?? 'sedentary',
      goalAdjustment: (json['goal_adjustment'] ?? 0).toDouble(),
      proteinRatio: (json['protein_ratio'] ?? 0.25).toDouble(),
      carbsRatio: (json['carbs_ratio'] ?? 0.45).toDouble(),
      fatRatio: (json['fat_ratio'] ?? 0.30).toDouble(),
    );
  }
  
  /// 取得活動量的中文名稱
  String get activityLevelLabel {
    switch (activityLevel) {
      case 'sedentary': return '久坐';
      case 'light': return '輕度活動';
      case 'moderate': return '中度活動';
      case 'active': return '高度活動';
      case 'very_active': return '非常活躍';
      default: return '久坐';
    }
  }
  
  /// 取得目標調整的描述
  String get goalAdjustmentLabel {
    if (goalAdjustment < 0) {
      return '減少 ${(-goalAdjustment * 100).toInt()}%';
    } else if (goalAdjustment > 0) {
      return '增加 ${(goalAdjustment * 100).toInt()}%';
    }
    return '維持';
  }
}

/// 今日飲食統計
class TodaySummary {
  final String userId;
  final String date;
  final int totalMeals;
  final ConsumedNutrients totalNutrients;
  final List<MealRecord> meals;

  TodaySummary({
    required this.userId,
    required this.date,
    required this.totalMeals,
    required this.totalNutrients,
    required this.meals,
  });

  factory TodaySummary.fromJson(Map<String, dynamic> json) {
    return TodaySummary(
      userId: json['user_id'] ?? '',
      date: json['date'] ?? '',
      totalMeals: json['total_meals'] ?? 0,
      totalNutrients: ConsumedNutrients.fromJson(json['total_nutrients'] ?? {}),
      meals: (json['meals'] as List<dynamic>?)
          ?.map((e) => MealRecord.fromJson(e))
          .toList() ?? [],
    );
  }
}

/// 已攝取的營養素
class ConsumedNutrients {
  final double calories;
  final double protein;
  final double carbs;
  final double fat;
  final double fiber;
  final double sodium;
  final double potassium;

  ConsumedNutrients({
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.fiber,
    required this.sodium,
    required this.potassium,
  });

  factory ConsumedNutrients.fromJson(Map<String, dynamic> json) {
    return ConsumedNutrients(
      calories: (json['calories'] ?? 0).toDouble(),
      protein: (json['protein'] ?? 0).toDouble(),
      carbs: (json['carbs'] ?? 0).toDouble(),
      fat: (json['fat'] ?? 0).toDouble(),
      fiber: (json['fiber'] ?? 0).toDouble(),
      sodium: (json['sodium'] ?? 0).toDouble(),
      potassium: (json['potassium'] ?? 0).toDouble(),
    );
  }
  
  /// 建立空的營養素（用於尚無資料時）
  factory ConsumedNutrients.empty() {
    return ConsumedNutrients(
      calories: 0, protein: 0, carbs: 0, fat: 0,
      fiber: 0, sodium: 0, potassium: 0,
    );
  }
}

/// 餐點紀錄
class MealRecord {
  final String mealId;
  final String? eatenAt;
  final String source;
  final String? note;
  final ConsumedNutrients nutrients;
  final List<MealItemRecord> items;

  MealRecord({
    required this.mealId,
    this.eatenAt,
    required this.source,
    this.note,
    required this.nutrients,
    required this.items,
  });

  factory MealRecord.fromJson(Map<String, dynamic> json) {
    return MealRecord(
      mealId: json['meal_id'] ?? '',
      eatenAt: json['eaten_at'],
      source: json['source'] ?? 'manual',
      note: json['note'],
      nutrients: ConsumedNutrients.fromJson(json['nutrients'] ?? {}),
      items: (json['items'] as List<dynamic>?)
          ?.map((e) => MealItemRecord.fromJson(e))
          .toList() ?? [],
    );
  }
  
  /// 取得餐點時間的格式化字串
  String get timeLabel {
    if (eatenAt == null) return '';
    try {
      final dt = DateTime.parse(eatenAt!);
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return '';
    }
  }
  
  /// 取得來源的中文名稱
  String get sourceLabel {
    switch (source) {
      case 'photo': return '📷 拍照辨識';
      case 'manual': return '✏️ 手動輸入';
      case 'voice': return '🎤 語音輸入';
      default: return source;
    }
  }
}

/// 餐點內的食物項目
class MealItemRecord {
  final String foodName;
  final double grams;
  final String? portionLabel;
  final ConsumedNutrients nutrients;

  MealItemRecord({
    required this.foodName,
    required this.grams,
    this.portionLabel,
    required this.nutrients,
  });

  factory MealItemRecord.fromJson(Map<String, dynamic> json) {
    return MealItemRecord(
      foodName: json['food_name'] ?? '',
      grams: (json['grams'] ?? 0).toDouble(),
      portionLabel: json['portion_label'],
      nutrients: ConsumedNutrients.fromJson(json['nutrients'] ?? {}),
    );
  }
  
  /// 取得份量描述
  String get portionDescription {
    if (portionLabel != null && portionLabel!.isNotEmpty) {
      return portionLabel!;
    }
    return '${grams.toInt()}g';
  }
}

/// 營養進度（結合目標和今日攝取）
class NutritionProgress {
  final NutritionTargets targets;
  final ConsumedNutrients consumed;
  final List<MealRecord> meals;
  final String date;

  NutritionProgress({
    required this.targets,
    required this.consumed,
    required this.meals,
    required this.date,
  });
  
  /// 熱量達成率 (0-1+)
  double get caloriesProgress => consumed.calories / targets.calories;
  
  /// 蛋白質達成率
  double get proteinProgress => consumed.protein / targets.proteinG;
  
  /// 碳水達成率
  double get carbsProgress => consumed.carbs / targets.carbsG;
  
  /// 脂肪達成率
  double get fatProgress => consumed.fat / targets.fatG;
  
  /// 纖維達成率
  double get fiberProgress => consumed.fiber / targets.fiberG;
  
  /// 剩餘熱量
  int get remainingCalories => targets.calories - consumed.calories.toInt();
  
  /// 是否已達標
  bool get isCaloriesReached => consumed.calories >= targets.calories;
  
  /// 建立 mock 資料（用於 UI 開發測試）
  factory NutritionProgress.mock() {
    return NutritionProgress(
      targets: NutritionTargets(
        calories: 2000,
        proteinG: 120,
        carbsG: 250,
        fatG: 67,
        fiberG: 28,
        bmr: 1650,
        tdee: 2000,
        activityLevel: 'light',
        goalAdjustment: 0,
        proteinRatio: 0.24,
        carbsRatio: 0.50,
        fatRatio: 0.26,
      ),
      consumed: ConsumedNutrients(
        calories: 1450,
        protein: 85,
        carbs: 180,
        fat: 48,
        fiber: 18,
        sodium: 1800,
        potassium: 2500,
      ),
      meals: [
        MealRecord(
          mealId: 'mock-1',
          eatenAt: DateTime.now().subtract(const Duration(hours: 6)).toIso8601String(),
          source: 'photo',
          note: '早餐',
          nutrients: ConsumedNutrients(
            calories: 450, protein: 25, carbs: 55, fat: 15,
            fiber: 5, sodium: 600, potassium: 800,
          ),
          items: [
            MealItemRecord(
              foodName: '全麥吐司',
              grams: 60,
              portionLabel: '2片',
              nutrients: ConsumedNutrients(
                calories: 150, protein: 6, carbs: 28, fat: 2,
                fiber: 3, sodium: 200, potassium: 100,
              ),
            ),
            MealItemRecord(
              foodName: '水煮蛋',
              grams: 100,
              portionLabel: '2顆',
              nutrients: ConsumedNutrients(
                calories: 150, protein: 12, carbs: 1, fat: 10,
                fiber: 0, sodium: 120, potassium: 130,
              ),
            ),
          ],
        ),
        MealRecord(
          mealId: 'mock-2',
          eatenAt: DateTime.now().subtract(const Duration(hours: 2)).toIso8601String(),
          source: 'manual',
          note: '午餐',
          nutrients: ConsumedNutrients(
            calories: 700, protein: 40, carbs: 85, fat: 22,
            fiber: 8, sodium: 900, potassium: 1200,
          ),
          items: [
            MealItemRecord(
              foodName: '雞腿便當',
              grams: 400,
              portionLabel: '1份',
              nutrients: ConsumedNutrients(
                calories: 700, protein: 40, carbs: 85, fat: 22,
                fiber: 8, sodium: 900, potassium: 1200,
              ),
            ),
          ],
        ),
      ],
      date: DateTime.now().toString().substring(0, 10),
    );
  }
}
