import 'package:flutter/material.dart';
import '../services/local_storage_service.dart';
import 'login_page.dart';
import 'home_shell.dart';

/// 啟動畫面：檢查登入狀態並導航
class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    _checkAuthAndNavigate();
  }

  Future<void> _checkAuthAndNavigate() async {
    // 延遲一秒顯示 Splash
    await Future.delayed(const Duration(seconds: 1));

    final storage = LocalStorageService.instance;
    final isLoggedIn = await storage.isLoggedIn();

    if (!mounted) return;

    if (isLoggedIn) {
      // 已登入，進入主頁
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomeShell()),
      );
    } else {
      // 未登入，進入登入頁
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const LoginPage()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F6),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.favorite,
              size: 80,
              color: Color(0xFF6B8E23),
            ),
            const SizedBox(height: 24),
            const Text(
              '🌿 My Health Coach',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Color(0xFF6B8E23),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '精準個人化健康管理',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade600,
              ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(
              color: Color(0xFF6B8E23),
            ),
          ],
        ),
      ),
    );
  }
}
