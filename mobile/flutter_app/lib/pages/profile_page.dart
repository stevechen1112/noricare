import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_service.dart';
import '../services/user_service.dart';
import '../state/app_state.dart';

class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController(text: 'Steve');
  final _ageController = TextEditingController(text: '40');
  final _heightController = TextEditingController(text: '178.8');
  final _weightController = TextEditingController(text: '78.8');

  String _gender = '男';
  String _activity = '幾乎不動 (久坐辦公)';
  String _dietPref = '無特殊偏好';

  final List<String> _habitOptions = [
    '外食族', '自己煮', '不吃早餐', '愛吃甜食', '常喝手搖飲', '常應酬喝酒'
  ];
  final List<String> _goalOptions = [
    '減重', '增肌', '控制血糖', '降低膽固醇', '提升精力'
  ];

  final Set<String> _selectedHabits = {'外食族'};
  final Set<String> _selectedGoals = {'控制血糖', '減重'};

  bool _loading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _ageController.dispose();
    _heightController.dispose();
    _weightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Form(
        key: _formKey,
        child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('建立/更新您的檔案', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          TextFormField(
            controller: _nameController,
            decoration: const InputDecoration(labelText: '姓名 *', border: OutlineInputBorder()),
            validator: (val) {
              if (val == null || val.trim().isEmpty) return '請輸入姓名';
              if (val.trim().length < 2) return '姓名至少需2個字元';
              return null;
            },
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _ageController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: '年齡 *', border: OutlineInputBorder()),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return '請輸入年齡';
                    final age = int.tryParse(val.trim());
                    if (age == null) return '請輸入有效數字';
                    if (age < 1 || age > 120) return '年齡需介於 1-120 歲';
                    return null;
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _gender,
                  decoration: const InputDecoration(labelText: '性別', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: '男', child: Text('男')),
                    DropdownMenuItem(value: '女', child: Text('女')),
                  ],
                  onChanged: (val) => setState(() => _gender = val ?? '男'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _heightController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: '身高 (cm) *', border: OutlineInputBorder()),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return '請輸入身高';
                    final height = double.tryParse(val.trim());
                    if (height == null) return '請輸入有效數字';
                    if (height < 50 || height > 250) return '身高需介於 50-250 cm';
                    return null;
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _weightController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: '體重 (kg) *', border: OutlineInputBorder()),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return '請輸入體重';
                    final weight = double.tryParse(val.trim());
                    if (weight == null) return '請輸入有效數字';
                    if (weight < 20 || weight > 300) return '體重需介於 20-300 kg';
                    return null;
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _activity,
            decoration: const InputDecoration(labelText: '平日活動量', border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: '幾乎不動 (久坐辦公)', child: Text('幾乎不動 (久坐辦公)')),
              DropdownMenuItem(value: '輕度活動 (偶爾散步)', child: Text('輕度活動 (偶爾散步)')),
              DropdownMenuItem(value: '中度活動 (規律運動 1-3次)', child: Text('中度活動 (規律運動 1-3次)')),
              DropdownMenuItem(value: '高度活動 (規律運動 3-5次)', child: Text('高度活動 (規律運動 3-5次)')),
            ],
            onChanged: (val) => setState(() => _activity = val ?? _activity),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _dietPref,
            decoration: const InputDecoration(labelText: '飲食偏好', border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: '無特殊偏好', child: Text('無特殊偏好')),
              DropdownMenuItem(value: '素食 (Vegetarian)', child: Text('素食 (Vegetarian)')),
              DropdownMenuItem(value: '生酮 (Keto)', child: Text('生酮 (Keto)')),
              DropdownMenuItem(value: '低醣 (Low Carb)', child: Text('低醣 (Low Carb)')),
            ],
            onChanged: (val) => setState(() => _dietPref = val ?? _dietPref),
          ),
          const SizedBox(height: 16),
          const Text('飲食習慣 (多選)', style: TextStyle(fontWeight: FontWeight.bold)),
          Wrap(
            spacing: 8,
            children: _habitOptions.map((h) {
              final selected = _selectedHabits.contains(h);
              return FilterChip(
                label: Text(h),
                selected: selected,
                onSelected: (val) => setState(() {
                  if (val) {
                    _selectedHabits.add(h);
                  } else {
                    _selectedHabits.remove(h);
                  }
                }),
              );
            }).toList(),
          ),
          const SizedBox(height: 12),
          const Text('健康目標 (多選)', style: TextStyle(fontWeight: FontWeight.bold)),
          Wrap(
            spacing: 8,
            children: _goalOptions.map((g) {
              final selected = _selectedGoals.contains(g);
              return FilterChip(
                label: Text(g),
                selected: selected,
                onSelected: (val) => setState(() {
                  if (val) {
                    _selectedGoals.add(g);
                  } else {
                    _selectedGoals.remove(g);
                  }
                }),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: _loading ? null : _saveProfile,
              icon: _loading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.save),
              label: const Text('儲存資料'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
                textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 2,
              ),
            ),
          ),
        ],
        ),
      ),
    );
  }

  Future<void> _saveProfile() async {
    final isLoggedIn = await AuthService().isLoggedIn();
    if (!isLoggedIn) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('請先登入再儲存 Profile')),
        );
      }
      return;
    }

    // 驗證表單
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final age = int.tryParse(_ageController.text.trim());
    final height = double.tryParse(_heightController.text.trim());
    final weight = double.tryParse(_weightController.text.trim());

    if (age == null || height == null || weight == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請填寫有效的年齡/身高/體重')),
      );
      return;
    }

    setState(() => _loading = true);

    final actMap = {
      '幾乎不動 (久坐辦公)': 'sedentary',
      '輕度活動 (偶爾散步)': 'light',
      '中度活動 (規律運動 1-3次)': 'moderate',
      '高度活動 (規律運動 3-5次)': 'active',
    };

    final payload = {
      'name': _nameController.text.trim(),
      'age': age,
      'gender': _gender == '男' ? 'male' : 'female',
      'height_cm': height,
      'weight_kg': weight,
      'health_goals': _selectedGoals.toList(),
      'lifestyle': {
        'activity_level': actMap[_activity] ?? 'sedentary',
        'dietary_preference': _dietPref,
        'eating_habits': _selectedHabits.toList(),
        'allergies': [],
      }
    };

    try {
      final result = await UserService().createUser(payload);
      ref.read(userProfileProvider.notifier).state = result;

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('已儲存使用者資料')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('儲存失敗：$e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}
