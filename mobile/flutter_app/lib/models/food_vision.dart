class FoodVisionSuggestItem {
  final String name;
  final double? confidence;
  final String? matchedFoodId;
  final String? matchedName;
  final String? matchedCategory;
  final double estimatedGrams;
  final double gramsMin;
  final double gramsMax;
  final String estimateLabel;
  final String? notes;

  FoodVisionSuggestItem({
    required this.name,
    required this.confidence,
    required this.matchedFoodId,
    required this.matchedName,
    required this.matchedCategory,
    required this.estimatedGrams,
    required this.gramsMin,
    required this.gramsMax,
    required this.estimateLabel,
    required this.notes,
  });

  factory FoodVisionSuggestItem.fromJson(Map<String, dynamic> json) {
    return FoodVisionSuggestItem(
      name: json['name'] ?? '',
      confidence: json['confidence'] == null ? null : (json['confidence'] as num).toDouble(),
      matchedFoodId: json['matched_food_id'],
      matchedName: json['matched_name'],
      matchedCategory: json['matched_category'],
      estimatedGrams: (json['estimated_grams'] ?? 0).toDouble(),
      gramsMin: (json['grams_min'] ?? 0).toDouble(),
      gramsMax: (json['grams_max'] ?? 0).toDouble(),
      estimateLabel: json['estimate_label'] ?? 'mid',
      notes: json['notes'],
    );
  }
}

class FoodVisionSuggestResponse {
  final List<FoodVisionSuggestItem> items;

  FoodVisionSuggestResponse({
    required this.items,
  });

  factory FoodVisionSuggestResponse.fromJson(Map<String, dynamic> json) {
    return FoodVisionSuggestResponse(
      items: (json['items'] as List<dynamic>? ?? [])
          .map((e) => FoodVisionSuggestItem.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
