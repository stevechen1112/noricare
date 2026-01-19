import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/user_service.dart';

final userProfileProvider = StateProvider<Map<String, dynamic>?>((ref) => null);
final profileReadyProvider = StateProvider<bool?>((ref) => null);
final reportProvider = StateProvider<Map<String, dynamic>?>((ref) => null);
final historyProvider = StateProvider<List<dynamic>>((ref) => []);
final healthDataProvider = StateProvider<Map<String, dynamic>>((ref) => {});
final abnormalItemsProvider = StateProvider<List<dynamic>>((ref) => []);
final chatHistoryProvider = StateProvider<List<Map<String, dynamic>>>((ref) => []);

/// Dashboard 資料 Provider (從 API 取得)
final dashboardProvider = StateProvider<DashboardData?>((ref) => null);

/// Dashboard 載入狀態
final dashboardLoadingProvider = StateProvider<bool>((ref) => false);

/// Dashboard 錯誤訊息
final dashboardErrorProvider = StateProvider<String?>((ref) => null);
