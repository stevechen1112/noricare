import 'package:shared_preferences/shared_preferences.dart';

/// 本地存儲服務：管理 Token、用戶資料等持久化數據
class LocalStorageService {
  static const String _tokenKey = 'auth_token';
  static const String _userIdKey = 'user_id';
  static const String _userNameKey = 'user_name';
  static const String _isLoggedInKey = 'is_logged_in';

  // Singleton
  LocalStorageService._internal();
  static final LocalStorageService instance = LocalStorageService._internal();

  SharedPreferences? _prefs;

  Future<void> init() async {
    _prefs ??= await SharedPreferences.getInstance();
  }

  // ===== Token 管理 =====
  Future<void> saveToken(String token) async {
    await init();
    await _prefs!.setString(_tokenKey, token);
  }

  Future<String?> getToken() async {
    await init();
    return _prefs!.getString(_tokenKey);
  }

  Future<void> clearToken() async {
    await init();
    await _prefs!.remove(_tokenKey);
  }

  // ===== 用戶資料 =====
  Future<void> saveUserInfo({
    required String userId,
    required String userName,
  }) async {
    await init();
    await _prefs!.setString(_userIdKey, userId);
    await _prefs!.setString(_userNameKey, userName);
    await _prefs!.setBool(_isLoggedInKey, true);
  }

  Future<Map<String, String?>> getUserInfo() async {
    await init();
    return {
      'user_id': _prefs!.getString(_userIdKey),
      'user_name': _prefs!.getString(_userNameKey),
    };
  }

  Future<bool> isLoggedIn() async {
    await init();
    return _prefs!.getBool(_isLoggedInKey) ?? false;
  }

  // ===== 登出 =====
  Future<void> logout() async {
    await init();
    await _prefs!.remove(_tokenKey);
    await _prefs!.remove(_userIdKey);
    await _prefs!.remove(_userNameKey);
    await _prefs!.setBool(_isLoggedInKey, false);
  }

  // ===== 清除所有數據 =====
  Future<void> clearAll() async {
    await init();
    await _prefs!.clear();
  }
}
