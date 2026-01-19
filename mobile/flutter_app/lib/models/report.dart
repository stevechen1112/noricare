class AdviceSection {
  final String title;
  final String content;
  final List<String> actionItems;

  AdviceSection({
    required this.title,
    required this.content,
    this.actionItems = const [],
  });

  factory AdviceSection.fromJson(Map<String, dynamic> json) {
    return AdviceSection(
      title: json['title'] as String? ?? '',
      content: json['content'] as String? ?? '',
      actionItems: (json['action_items'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

class NutritionReport {
  NutritionReport({
    required this.reportId,
    required this.healthScore,
    required this.foodAdvice,
    required this.supplementAdvice,
    required this.mealPlan,
  });

  final String reportId;
  final int? healthScore;
  final List<AdviceSection> foodAdvice;
  final List<AdviceSection> supplementAdvice;
  final Map<String, dynamic> mealPlan;

  factory NutritionReport.fromJson(Map<String, dynamic> json) {
    return NutritionReport(
      reportId: json['report_id']?.toString() ?? '',
      healthScore: json['health_score'] as int?,
      foodAdvice: (json['food_advice'] as List<dynamic>?)
          ?.map((e) => AdviceSection.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      supplementAdvice: (json['supplement_advice'] as List<dynamic>?)
          ?.map((e) => AdviceSection.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      mealPlan: json['meal_plan'] as Map<String, dynamic>? ?? {},
    );
  }
}
