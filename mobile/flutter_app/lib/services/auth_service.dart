import 'api_client.dart';
import 'local_storage_service.dart';

/// 認證服務：處理登入、註冊、登出
class AuthService {
  final _storage = LocalStorageService.instance;

  /// 註冊新用戶
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String name,
  }) async {
    try {
      final response = await ApiClient.instance.dio.post(
        '/auth/register',
        data: {
          'email': email,
          'password': password,
          'name': name,
        },
      );

      final data = response.data as Map<String, dynamic>;

      // 儲存 Token 和用戶資料
      if (data['token'] != null) {
        await _storage.saveToken(data['token']);
      }
      if (data['user'] != null) {
        final user = data['user'] as Map<String, dynamic>;
        await _storage.saveUserInfo(
          userId: user['id']?.toString() ?? '',
          userName: user['name']?.toString() ?? name,
        );
      }

      return data;
    } catch (e) {
      rethrow;
    }
  }

  /// 登入
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await ApiClient.instance.dio.post(
        '/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );

      final data = response.data as Map<String, dynamic>;

      // 儲存 Token 和用戶資料
      if (data['token'] != null) {
        await _storage.saveToken(data['token']);
      }
      if (data['user'] != null) {
        final user = data['user'] as Map<String, dynamic>;
        await _storage.saveUserInfo(
          userId: user['id']?.toString() ?? '',
          userName: user['name']?.toString() ?? '',
        );
      }

      return data;
    } catch (e) {
      rethrow;
    }
  }

  /// 登出
  Future<void> logout() async {
    await _storage.logout();
  }

  /// 檢查是否已登入
  Future<bool> isLoggedIn() async {
    return await _storage.isLoggedIn();
  }

  /// 獲取當前用戶資料
  Future<Map<String, String?>> getCurrentUser() async {
    return await _storage.getUserInfo();
  }

  /// 獲取 Token
  Future<String?> getToken() async {
    return await _storage.getToken();
  }
}
