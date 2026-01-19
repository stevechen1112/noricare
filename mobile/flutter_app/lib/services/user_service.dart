import 'package:dio/dio.dart';
import 'api_client.dart';

class UserService {
  final Dio _dio = ApiClient.instance.dio;

  Future<Map<String, dynamic>> createUser(Map<String, dynamic> payload) async {
    try {
      final response = await _dio.post('/users/', data: payload);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('請先登入');
      }
      rethrow;
    }
  }

  /// 取得當前使用者的 Dashboard 資料
  /// 包含 health_score、key_metrics、abnormal_items、history
  Future<DashboardData> getMyDashboard() async {
    try {
      final response = await _dio.get('/users/me/dashboard');
      return DashboardData.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 400) {
        throw Exception('請先完成健康檔案設定');
      } else if (e.response?.statusCode == 401) {
        throw Exception('尚未登入');
      }
      rethrow;
    }
  }
}

/// Dashboard 資料模型
class DashboardData {
  final String userId;
  final String? latestRecordDate;
  final int? healthScore;
  final List<DashboardKeyMetric> keyMetrics;
  final List<DashboardAbnormalItem> abnormalItems;
  final List<DashboardHistoryItem> history;
  final Map<String, dynamic>? aiReport; // 新增：AI 分析報告

  DashboardData({
    required this.userId,
    this.latestRecordDate,
    this.healthScore,
    required this.keyMetrics,
    required this.abnormalItems,
    required this.history,
    this.aiReport,
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    // 更穩健地解析 health_score (可能是 int, double, 或 null)
    int? parseHealthScore(dynamic value) {
      if (value == null) return null;
      if (value is int) return value;
      if (value is double) return value.round();
      if (value is String) return int.tryParse(value);
      return null;
    }

    return DashboardData(
      userId: json['user_id'] as String,
      latestRecordDate: json['latest_record_date'] as String?,
      healthScore: parseHealthScore(json['health_score']),
      keyMetrics: (json['key_metrics'] as List<dynamic>?)
              ?.map((e) => DashboardKeyMetric.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      abnormalItems: (json['abnormal_items'] as List<dynamic>?)
              ?.map((e) => DashboardAbnormalItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      history: (json['history'] as List<dynamic>?)
              ?.map((e) => DashboardHistoryItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      aiReport: json['ai_report'] as Map<String, dynamic>?,
    );
  }
}

class DashboardKeyMetric {
  final String label;
  final dynamic value;
  final String? unit;
  final String status; // normal|caution|warning|danger

  DashboardKeyMetric({
    required this.label,
    required this.value,
    this.unit,
    this.status = 'normal',
  });

  factory DashboardKeyMetric.fromJson(Map<String, dynamic> json) {
    return DashboardKeyMetric(
      label: json['label'] as String,
      value: json['value'],
      unit: json['unit'] as String?,
      status: json['status'] as String? ?? 'normal',
    );
  }
}

class DashboardAbnormalItem {
  final String name;
  final dynamic value;
  final String? unit;
  final String severity; // caution|warning|danger
  final String? normalRange;

  DashboardAbnormalItem({
    required this.name,
    required this.value,
    this.unit,
    this.severity = 'warning',
    this.normalRange,
  });

  factory DashboardAbnormalItem.fromJson(Map<String, dynamic> json) {
    return DashboardAbnormalItem(
      name: json['name'] as String,
      value: json['value'],
      unit: json['unit'] as String?,
      severity: json['severity'] as String? ?? 'warning',
      normalRange: json['normal_range'] as String?,
    );
  }
}

class DashboardHistoryItem {
  final String recordId;
  final String createdAt;
  final int? healthScore;
  final Map<String, double> keyMetrics;

  DashboardHistoryItem({
    required this.recordId,
    required this.createdAt,
    this.healthScore,
    required this.keyMetrics,
  });

  factory DashboardHistoryItem.fromJson(Map<String, dynamic> json) {
    return DashboardHistoryItem(
      recordId: json['record_id'] as String,
      createdAt: json['created_at'] as String,
      healthScore: json['health_score'] as int?,
      keyMetrics: (json['key_metrics'] as Map<String, dynamic>?)
              ?.map((k, v) => MapEntry(k, (v as num).toDouble())) ??
          {},
    );
  }
}
