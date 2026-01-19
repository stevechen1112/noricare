import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/meal.dart';
import '../services/meal_service.dart';
import '../services/nutrition_service.dart';
import 'meal_photo_suggest_page.dart';

class MealLogPage extends ConsumerStatefulWidget {
  const MealLogPage({super.key});

  @override
  ConsumerState<MealLogPage> createState() => _MealLogPageState();
}

class _MealLogPageState extends ConsumerState<MealLogPage> {
  final MealService _mealService = MealService();
  final NutritionService _nutritionService = NutritionService();
  final TextEditingController _foodController = TextEditingController();

  // 設為 false 時會使用真實 API 數據
  static const bool _useMockData = false;

  double _grams = 100;
  List<FoodMatch> _alignResults = [];
  FoodMatch? _selectedMatch;
  List<MealItemDraft> _draftItems = [];
  List<MealResponse> _recentMeals = [];
  bool _loading = false;
  
  // 方案 B: 營養進度數據
  NutritionProgress? _nutritionProgress;
  String? _nutritionError;

  @override
  void initState() {
    super.initState();
    _loadNutritionProgress();
  }

  @override
  void dispose() {
    _foodController.dispose();
    super.dispose();
  }
  
  /// 載入營養進度（目標 + 今日攝取）
  Future<void> _loadNutritionProgress() async {
    if (_useMockData) {
      setState(() {
        _nutritionProgress = NutritionProgress.mock();
        _nutritionError = null;
      });
      return;
    }
    
    setState(() {
      _loading = true;
      _nutritionError = null;
    });
    
    try {
      final progress = await _nutritionService.getTodayProgress();
      setState(() {
        _nutritionProgress = progress;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _nutritionError = e.toString();
        _loading = false;
        _nutritionProgress = null;
      });
    }
  }

  Future<void> _loadSummary() async {
    final recent = await _mealService.listMeals(limit: 10);
    setState(() {
      _recentMeals = recent;
    });
  }

  Future<void> _alignFood() async {
    if (_foodController.text.trim().isEmpty) return;
    setState(() => _loading = true);
    try {
      final result = await _mealService.alignFood(_foodController.text.trim(), limit: 5);
      setState(() {
        _alignResults = result.results;
        _selectedMatch = result.results.isNotEmpty ? result.results.first : null;
      });
    } finally {
      setState(() => _loading = false);
    }
  }

  void _addDraftItem() {
    if (_selectedMatch == null) return;
    setState(() {
      _draftItems.add(MealItemDraft(
        foodId: _selectedMatch!.foodId,
        foodName: _selectedMatch!.name,
        grams: _grams,
      ));
    });
  }

  Future<void> _saveMeal() async {
    if (_draftItems.isEmpty) return;
    setState(() => _loading = true);
    try {
      await _mealService.createMeal(items: _draftItems);
      setState(() {
        _draftItems = [];
      });
      // 儲存後重新載入營養進度
      await _loadNutritionProgress();
      await _loadSummary();
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () async {
        await _loadNutritionProgress();
        await _loadSummary();
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 錯誤提示
          if (_nutritionError != null) ...[
            Card(
              color: Colors.orange[50],
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    Icon(Icons.warning, color: Colors.orange[700]),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '無法取得營養目標，請先儲存 Profile 或登入',
                        style: TextStyle(color: Colors.orange[900]),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
          
          // 今日營養攝取總覽
          const Text('今日營養攝取', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildNutritionOverview(),
          const SizedBox(height: 24),
          
          // 三大營養素比例
          const Text('營養素組成', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildMacrosPieChart(),
          const SizedBox(height: 24),
          
          // 拍照辨識
          _buildPhotoRecognitionCard(),
          const SizedBox(height: 24),
          
          // 手動記錄
          const Text('手動記錄食物', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildManualInput(),
          
          // 最近餐點
          const SizedBox(height: 24),
          const Text('最近餐點', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          _buildRecentMeals(),
        ],
      ),
    );
  }

  // 營養攝取總覽（進度條）
  Widget _buildNutritionOverview() {
    if (_nutritionProgress == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }
    
    final progress = _nutritionProgress!;
    final targets = progress.targets;
    final consumed = progress.consumed;
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // 顯示剩餘熱量
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  progress.remainingCalories > 0 
                    ? '還可攝取' 
                    : '已超過',
                  style: const TextStyle(fontSize: 14),
                ),
                const SizedBox(width: 4),
                Text(
                  '${progress.remainingCalories.abs()}',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: progress.remainingCalories > 0 
                      ? Theme.of(context).primaryColor 
                      : Colors.orange[700],
                  ),
                ),
                const SizedBox(width: 4),
                const Text('kcal', style: TextStyle(fontSize: 14)),
              ],
            ),
            const SizedBox(height: 16),
            _buildNutrientBar('熱量', consumed.calories, 
                              targets.calories.toDouble(), 'kcal', Colors.orange),
            const SizedBox(height: 16),
            _buildNutrientBar('蛋白質', consumed.protein, 
                              targets.proteinG.toDouble(), 'g', Colors.red),
            const SizedBox(height: 16),
            _buildNutrientBar('碳水化合物', consumed.carbs, 
                              targets.carbsG.toDouble(), 'g', Colors.blue),
            const SizedBox(height: 16),
            _buildNutrientBar('脂肪', consumed.fat, 
                              targets.fatG.toDouble(), 'g', Colors.amber),
          ],
        ),
      ),
    );
  }

  // 營養素進度條
  Widget _buildNutrientBar(String label, double actual, double target, String unit, Color color) {
    final percentage = (actual / target * 100).clamp(0, 100);
    final isOver = actual > target;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
            ),
            Row(
              children: [
                Text(
                  actual.toStringAsFixed(0),
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: isOver ? Colors.orange[700] : color,
                  ),
                ),
                Text(
                  ' / ${target.toStringAsFixed(0)} $unit',
                  style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                ),
              ],
            ),
          ],
        ),
        const SizedBox(height: 8),
        Stack(
          children: [
            Container(
              height: 8,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            FractionallySizedBox(
              widthFactor: percentage / 100,
              child: Container(
                height: 8,
                decoration: BoxDecoration(
                  color: isOver ? Colors.orange[700] : color,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          isOver 
            ? '超出 ${(actual - target).toStringAsFixed(0)} $unit' 
            : '還可攝取 ${(target - actual).toStringAsFixed(0)} $unit',
          style: TextStyle(
            fontSize: 12,
            color: isOver ? Colors.orange[700] : Colors.grey[600],
          ),
        ),
      ],
    );
  }

  // 三大營養素圓餅圖
  Widget _buildMacrosPieChart() {
    if (_nutritionProgress == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }
    
    final consumed = _nutritionProgress!.consumed;
    final protein = consumed.protein;
    final carbs = consumed.carbs;
    final fat = consumed.fat;
    
    // 計算卡路里佔比（蛋白質和碳水各4kcal/g，脂肪9kcal/g）
    final proteinCal = protein * 4;
    final carbsCal = carbs * 4;
    final fatCal = fat * 9;
    final totalCal = proteinCal + carbsCal + fatCal;
    
    // 如果還沒有攝取，顯示提示
    if (totalCal == 0) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Center(
            child: Column(
              children: [
                Icon(Icons.pie_chart, size: 48, color: Colors.grey[300]),
                const SizedBox(height: 12),
                Text(
                  '今日尚無攝取紀錄',
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ],
            ),
          ),
        ),
      );
    }
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            // 圓餅圖
            SizedBox(
              width: 140,
              height: 140,
              child: PieChart(
                PieChartData(
                  sectionsSpace: 2,
                  centerSpaceRadius: 35,
                  sections: [
                    PieChartSectionData(
                      value: proteinCal,
                      title: '${(proteinCal / totalCal * 100).toStringAsFixed(0)}%',
                      color: Colors.red,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    PieChartSectionData(
                      value: carbsCal,
                      title: '${(carbsCal / totalCal * 100).toStringAsFixed(0)}%',
                      color: Colors.blue,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    PieChartSectionData(
                      value: fatCal,
                      title: '${(fatCal / totalCal * 100).toStringAsFixed(0)}%',
                      color: Colors.amber,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 24),
            // 圖例
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildLegendItem('蛋白質', protein, 'g', Colors.red),
                  const SizedBox(height: 12),
                  _buildLegendItem('碳水化合物', carbs, 'g', Colors.blue),
                  const SizedBox(height: 12),
                  _buildLegendItem('脂肪', fat, 'g', Colors.amber),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(String label, double value, String unit, Color color) {
    return Row(
      children: [
        Container(
          width: 16,
          height: 16,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(fontSize: 14),
        ),
        const Spacer(),
        Text(
          '${value.toStringAsFixed(0)} $unit',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  // 拍照辨識卡片
  Widget _buildPhotoRecognitionCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('拍照辨識（AI 粗估份量）', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            const Text('上傳食物照片，AI 會自動辨識並估算份量。'),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.camera_alt),
                label: const Text('拍照 / 上傳照片'),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const MealPhotoSuggestPage()),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  // 手動輸入區
  Widget _buildManualInput() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _foodController,
              decoration: const InputDecoration(
                labelText: '食物名稱（例如：水煮雞胸肉、白飯）',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Slider(
                    value: _grams,
                    min: 10,
                    max: 500,
                    divisions: 98,
                    label: '${_grams.toStringAsFixed(0)} g',
                    onChanged: (value) => setState(() => _grams = value),
                  ),
                ),
                const SizedBox(width: 12),
                Text('${_grams.toStringAsFixed(0)} g'),
              ],
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: _loading ? null : _alignFood,
              icon: const Icon(Icons.search),
              label: const Text('對齊食物'),
            ),
            if (_alignResults.isNotEmpty) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<FoodMatch>(
                value: _selectedMatch,
                items: _alignResults
                    .map((e) => DropdownMenuItem(
                          value: e,
                          child: Text('${e.name} (${e.category})  score=${e.score}'),
                        ))
                    .toList(),
                onChanged: (value) => setState(() => _selectedMatch = value),
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: '選擇匹配結果',
                ),
              ),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: _selectedMatch == null ? null : _addDraftItem,
                icon: const Icon(Icons.add),
                label: const Text('加入餐點'),
              ),
            ],
            if (_draftItems.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text('餐點清單', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ..._draftItems.map((e) => ListTile(
                    title: Text(e.foodName),
                    subtitle: Text('${e.grams.toStringAsFixed(0)} g'),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete),
                      onPressed: () {
                        setState(() => _draftItems.remove(e));
                      },
                    ),
                  )),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _loading ? null : () => _saveMeal(),
                  child: const Text('儲存這一餐'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // 最近餐點
  Widget _buildRecentMeals() {
    // 使用營養進度中的 meals 數據
    if (_nutritionProgress != null && _nutritionProgress!.meals.isNotEmpty) {
      return Column(
        children: _nutritionProgress!.meals.map((meal) {
          // 加入 Dismissible 左滑刪除
          return Dismissible(
            key: Key(meal.mealId),
            direction: DismissDirection.endToStart,
            background: Container(
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.only(right: 20),
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: Colors.red,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.delete, color: Colors.white, size: 32),
                  SizedBox(height: 4),
                  Text(
                    '刪除',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
            confirmDismiss: (direction) async {
              if (meal.mealId.isEmpty) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('無法刪除：缺少餐點 ID')),
                  );
                }
                return false;
              }
              // 確認對話框
              return await showDialog<bool>(
                context: context,
                builder: (BuildContext context) {
                  return AlertDialog(
                    title: const Text('確認刪除'),
                    content: Text('確定要刪除「${meal.timeLabel}」的記錄嗎？'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(false),
                        child: const Text('取消'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(true),
                        style: TextButton.styleFrom(foregroundColor: Colors.red),
                        child: const Text('刪除'),
                      ),
                    ],
                  );
                },
              );
            },
            onDismissed: (direction) async {
              try {
                await _mealService.deleteMeal(meal.mealId);
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('刪除失敗：$e')),
                  );
                }
                await _loadNutritionProgress();
                return;
              }
              
              // 顯示 SnackBar
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('已刪除「${meal.timeLabel}」'),
                    action: SnackBarAction(
                      label: '復原',
                      onPressed: () {
                        _loadNutritionProgress();
                      },
                    ),
                  ),
                );
              }
              
              // 重新載入數據
              await _loadNutritionProgress();
            },
            child: Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: ExpansionTile(
                leading: Icon(
                  meal.source == 'photo' ? Icons.camera_alt : Icons.edit,
                  color: Theme.of(context).primaryColor,
                ),
                title: Row(
                  children: [
                    Text(meal.timeLabel),
                    if (meal.note != null && meal.note!.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      Text(
                        meal.note!,
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ],
                ),
                subtitle: Row(
                  children: [
                    Text(meal.sourceLabel),
                    const SizedBox(width: 12),
                    Text(
                      '${meal.nutrients.calories.toStringAsFixed(0)} kcal',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
                children: meal.items.isEmpty
                    ? [
                        ListTile(
                          dense: true,
                          leading: const Icon(Icons.circle, size: 8),
                          title: Text('熱量 ${meal.nutrients.calories.toStringAsFixed(0)} kcal'),
                        ),
                      ]
                    : meal.items.map((item) {
                        return ListTile(
                          dense: true,
                          leading: const Icon(Icons.circle, size: 8),
                          title: Text(item.foodName),
                          subtitle: Text('${item.portionDescription} · ${item.nutrients.calories.toStringAsFixed(0)} kcal'),
                        );
                      }).toList(),
              ),
            ),
          );
        }).toList(),
      );
    }
    
    // 如果沒有營養進度中的餐點，顯示空狀態或 API 餐點
    if (_recentMeals.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Center(
            child: Column(
              children: [
                Icon(Icons.restaurant, size: 48, color: Colors.grey[400]),
                const SizedBox(height: 12),
                Text(
                  '今日尚無餐點紀錄',
                  style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                ),
                const SizedBox(height: 8),
                Text(
                  '透過拍照或手動輸入來記錄您的飲食',
                  style: TextStyle(fontSize: 13, color: Colors.grey[500]),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Column(
      children: _recentMeals.map((meal) => Card(
        margin: const EdgeInsets.only(bottom: 12),
        child: ExpansionTile(
          title: Text(meal.eatenAt),
          subtitle: Text('來源：${meal.source}'),
          children: meal.items
              .map((item) => ListTile(
                    title: Text(item.foodName),
                    subtitle: Text('${item.grams.toStringAsFixed(0)} g'),
                  ))
              .toList(),
        ),
      )).toList(),
    );
  }
}
