class FoodMatch {
  final String foodId;
  final String name;
  final String category;
  final String matchedField;
  final double score;

  FoodMatch({
    required this.foodId,
    required this.name,
    required this.category,
    required this.matchedField,
    required this.score,
  });

  factory FoodMatch.fromJson(Map<String, dynamic> json) {
    return FoodMatch(
      foodId: json['food_id'] ?? '',
      name: json['name'] ?? '',
      category: json['category'] ?? '',
      matchedField: json['matched_field'] ?? '',
      score: (json['score'] ?? 0).toDouble(),
    );
  }
}

class FoodAlignResponse {
  final String query;
  final int count;
  final List<FoodMatch> results;

  FoodAlignResponse({
    required this.query,
    required this.count,
    required this.results,
  });

  factory FoodAlignResponse.fromJson(Map<String, dynamic> json) {
    return FoodAlignResponse(
      query: json['query'] ?? '',
      count: json['count'] ?? 0,
      results: (json['results'] as List<dynamic>? ?? [])
          .map((e) => FoodMatch.fromJson(e))
          .toList(),
    );
  }
}

class Nutrients {
  final double calories;
  final double protein;
  final double carbs;
  final double fat;
  final double sodium;
  final double fiber;
  final double potassium;

  Nutrients({
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.sodium,
    required this.fiber,
    required this.potassium,
  });

  factory Nutrients.fromJson(Map<String, dynamic> json) {
    return Nutrients(
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

class MealItemResponse {
  final String mealItemId;
  final String foodId;
  final String foodName;
  final double grams;
  final String? portionLabel;
  final double? confidence;
  final Nutrients nutrients;

  MealItemResponse({
    required this.mealItemId,
    required this.foodId,
    required this.foodName,
    required this.grams,
    required this.portionLabel,
    required this.confidence,
    required this.nutrients,
  });

  factory MealItemResponse.fromJson(Map<String, dynamic> json) {
    return MealItemResponse(
      mealItemId: json['meal_item_id'] ?? '',
      foodId: json['food_id'] ?? '',
      foodName: json['food_name'] ?? '',
      grams: (json['grams'] ?? 0).toDouble(),
      portionLabel: json['portion_label'],
      confidence: json['confidence'] == null ? null : (json['confidence'] as num).toDouble(),
      nutrients: Nutrients.fromJson(json['nutrients'] ?? {}),
    );
  }
}

class MealResponse {
  final String mealId;
  final String userId;
  final String eatenAt;
  final String source;
  final String? note;
  final Nutrients nutrients;
  final List<MealItemResponse> items;

  MealResponse({
    required this.mealId,
    required this.userId,
    required this.eatenAt,
    required this.source,
    required this.note,
    required this.nutrients,
    required this.items,
  });

  factory MealResponse.fromJson(Map<String, dynamic> json) {
    return MealResponse(
      mealId: json['meal_id'] ?? '',
      userId: json['user_id'] ?? '',
      eatenAt: json['eaten_at'] ?? '',
      source: json['source'] ?? 'manual',
      note: json['note'],
      nutrients: Nutrients.fromJson(json['nutrients'] ?? {}),
      items: (json['items'] as List<dynamic>? ?? [])
          .map((e) => MealItemResponse.fromJson(e))
          .toList(),
    );
  }
}

class MealSummaryResponse {
  final String userId;
  final int days;
  final int totalMeals;
  final Nutrients totalNutrients;
  final List<Map<String, Nutrients>> dailyBreakdown;

  MealSummaryResponse({
    required this.userId,
    required this.days,
    required this.totalMeals,
    required this.totalNutrients,
    required this.dailyBreakdown,
  });

  factory MealSummaryResponse.fromJson(Map<String, dynamic> json) {
    final breakdown = <Map<String, Nutrients>>[];
    for (final item in (json['daily_breakdown'] as List<dynamic>? ?? [])) {
      final map = <String, Nutrients>{};
      (item as Map<String, dynamic>).forEach((key, value) {
        map[key] = Nutrients.fromJson(value);
      });
      breakdown.add(map);
    }

    return MealSummaryResponse(
      userId: json['user_id'] ?? '',
      days: json['days'] ?? 7,
      totalMeals: json['total_meals'] ?? 0,
      totalNutrients: Nutrients.fromJson(json['total_nutrients'] ?? {}),
      dailyBreakdown: breakdown,
    );
  }
}

class MealItemDraft {
  final String foodId;
  final String foodName;
  final double grams;

  MealItemDraft({
    required this.foodId,
    required this.foodName,
    required this.grams,
  });
}
