/// API Configuration for different environments
/// 
/// 使用方式：
/// - 開發環境：flutter run （預設）
/// - 測試環境：flutter run --dart-define=ENV=staging
/// - 正式環境：flutter run --dart-define=ENV=production
/// - Web 部署：flutter build web --dart-define=ENV=production
/// 
/// 建置 Release 版本：
/// - flutter build apk --dart-define=ENV=production
/// - flutter build appbundle --dart-define=ENV=production
/// - flutter build ios --dart-define=ENV=production
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiConfig {
  // 🔧 從編譯時環境變數讀取
  static const String environment = String.fromEnvironment(
    'ENV',
    defaultValue: 'development',
  );

  /// API 基礎 URL（根據環境自動切換）
  static String get baseUrl {
    // 🌐 Web 版本使用相對路徑（Caddy 反向代理）
    if (kIsWeb && environment == 'production') {
      return '/api/v1';
    }
    
    switch (environment) {
      case 'production':
        // 原生 App 使用完整 URL
        return const String.fromEnvironment(
          'API_BASE_URL',
          defaultValue: 'https://noricare.app/api/v1',
        );
      case 'staging':
        return const String.fromEnvironment(
          'API_BASE_URL',
          defaultValue: 'https://staging-api.myhealthcoach.com/api/v1',
        );
      case 'development':
      default:
        // 💡 本地開發預設值
        // 若需真機測試，請改成您的電腦 IP
        // 或使用：flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000/api/v1
        return const String.fromEnvironment(
          'API_BASE_URL',
          defaultValue: 'http://localhost:8000/api/v1',
        );
    }
  }

  // API 超時設定
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration aiGenerateTimeout = Duration(minutes: 2);
  
  // 重試設定
  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 1);

  // Debug 模式
  static bool get isDebug => environment != 'production';
  
  // 版本資訊
  static const String appVersion = '1.0.0';
  static const int buildNumber = 1;
}

/// 環境狀態小工具（僅 Debug 時顯示）
class EnvironmentBanner {
  static String get label {
    switch (ApiConfig.environment) {
      case 'production':
        return ''; // 正式環境不顯示標籤
      case 'staging':
        return '🧪 STAGING';
      default:
        return '🔧 DEV';
    }
  }
  
  static bool get shouldShow => ApiConfig.environment != 'production';
}
