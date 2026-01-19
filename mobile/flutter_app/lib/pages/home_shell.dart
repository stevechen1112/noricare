import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../app_theme.dart';
import '../services/local_storage_service.dart';
import '../services/auth_service.dart';
import '../services/user_service.dart';
import '../state/app_state.dart';
import 'profile_page.dart';
import 'upload_page.dart';
import 'dashboard_page.dart';
import 'chat_page.dart';
import 'login_page.dart';
import 'nutrition_search_page.dart';
import 'meal_log_page.dart';

class HomeShell extends ConsumerStatefulWidget {
  const HomeShell({super.key});

  @override
  ConsumerState<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends ConsumerState<HomeShell> {
  int _currentStep = 0;
  bool _checkingProfile = false;

  final List<Widget> _pages = [
    const ProfilePage(),
    const UploadPage(),
    const DashboardPage(),
    const ChatPage(),
    const MealLogPage(),
  ];

  @override
  void initState() {
    super.initState();
    _loadProfileStatus();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🌿 My Health Coach'),
        actions: [
          // 營養查詢入口（Phase 1 驗證功能）
          IconButton(
            icon: const Icon(Icons.food_bank_outlined),
            tooltip: '營養查詢',
            onPressed: () {
              _ensureProfileThen(() {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const NutritionSearchPage()),
                );
              });
            },
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (value) {
              if (value == 'logout') {
                _confirmLogout();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, color: Colors.red),
                    SizedBox(width: 8),
                    Text('登出'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          _stepperHeader(),
          const Divider(height: 1),
          Expanded(child: _pages[_currentStep]),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentStep,
        onTap: _handleNavTap,
        selectedItemColor: AppTheme.primary,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
          BottomNavigationBarItem(icon: Icon(Icons.upload_file), label: 'Upload'),
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.chat), label: 'Chat'),
          BottomNavigationBarItem(icon: Icon(Icons.restaurant_menu), label: 'Meals'),
        ],
      ),
    );
  }

  Future<void> _handleNavTap(int index) async {
    if (index == 0) {
      setState(() => _currentStep = index);
      return;
    }

    final hasProfile = await _ensureProfileReady();
    if (!hasProfile) {
      final goProfile = await _showProfileRequiredDialog();
      if (goProfile == true && mounted) {
        setState(() => _currentStep = 0);
      }
      return;
    }

    setState(() => _currentStep = index);
  }

  Future<void> _ensureProfileThen(VoidCallback action) async {
    final hasProfile = await _ensureProfileReady();
    if (!hasProfile) {
      final goProfile = await _showProfileRequiredDialog();
      if (goProfile == true && mounted) {
        setState(() => _currentStep = 0);
      }
      return;
    }
    action();
  }

  Future<bool> _ensureProfileReady() async {
    final status = ref.read(profileReadyProvider);
    if (status != null) return status;
    await _loadProfileStatus();
    return ref.read(profileReadyProvider) ?? false;
  }

  Future<void> _loadProfileStatus() async {
    if (_checkingProfile) return;
    _checkingProfile = true;
    try {
      final token = await AuthService().getToken();
      if (token == null || token.isEmpty) {
        ref.read(profileReadyProvider.notifier).state = false;
        return;
      }

      try {
        final dashboard = await UserService().getMyDashboard();
        ref.read(profileReadyProvider.notifier).state = true;
        ref.read(userProfileProvider.notifier).state = {
          'id': dashboard.userId,
        };
      } catch (e) {
        ref.read(profileReadyProvider.notifier).state = false;
      }
    } finally {
      _checkingProfile = false;
    }
  }

  Future<bool?> _showProfileRequiredDialog() {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('請先完成基本資料'),
        content: const Text('完成 Profile 後才能使用其他功能。是否現在前往填寫？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('前往填寫'),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('登出'),
        content: const Text('確定要登出嗎？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('登出', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed != true) return;
    await LocalStorageService.instance.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginPage()),
      (route) => false,
    );
  }

  Widget _stepperHeader() {
    final labels = ['Profile', 'Upload', 'Dashboard', 'Chat', 'Meals'];
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: List.generate(labels.length, (index) {
          final active = index == _currentStep;
          return Column(
            children: [
              CircleAvatar(
                radius: 14,
                backgroundColor: active ? AppTheme.primary : Colors.grey.shade300,
                child: Text(
                  '${index + 1}',
                  style: TextStyle(
                    color: active ? Colors.white : Colors.black54,
                    fontSize: 12,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                labels[index],
                style: TextStyle(
                  fontSize: 12,
                  color: active ? AppTheme.primary : Colors.black54,
                ),
              ),
            ],
          );
        }),
      ),
    );
  }
}
