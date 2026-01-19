class HealthHistoryItem {
  HealthHistoryItem({required this.date, required this.score});

  final String date;
  final int? score;

  factory HealthHistoryItem.fromJson(Map<String, dynamic> json) {
    return HealthHistoryItem(
      date: json['created_at'] as String,
      score: json['health_score'] as int?,
    );
  }
}
