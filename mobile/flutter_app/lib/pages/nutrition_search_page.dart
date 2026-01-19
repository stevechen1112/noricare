import 'package:flutter/material.dart';
import '../services/nutrition_service.dart';

/// 營養查詢頁面 (Phase 1 MVP)
/// 獨立頁面，用於驗證資料庫整合的價值
/// 如果驗證失敗，可以直接移除而不影響主系統
class NutritionSearchPage extends StatefulWidget {
  const NutritionSearchPage({super.key});

  @override
  State<NutritionSearchPage> createState() => _NutritionSearchPageState();
}

class _NutritionSearchPageState extends State<NutritionSearchPage> {
  final NutritionService _service = NutritionService();
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _gramsController = TextEditingController(text: '100');

  List<FoodNutrition> _searchResults = [];
  CalculatedNutrients? _calculatedResult;
  NutritionStats? _stats;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    try {
      final stats = await _service.getStats();
      setState(() => _stats = stats);
    } catch (e) {
      // 統計載入失敗不影響主功能
    }
  }

  Future<void> _search() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _calculatedResult = null;
    });

    try {
      final result = await _service.searchFood(query);
      setState(() {
        _searchResults = result.results;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _calculate(String foodName) async {
    final grams = double.tryParse(_gramsController.text) ?? 100;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _service.calculateNutrients(foodName, grams);
      setState(() {
        _calculatedResult = result;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('營養成分查詢'),
        backgroundColor: Colors.green.shade700,
        foregroundColor: Colors.white,
        actions: [
          if (_stats != null)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(
                child: Text(
                  '${_stats!.totalFoods} 食物',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // 搜尋區域
          Container(
            color: Colors.green.shade50,
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      flex: 3,
                      child: TextField(
                        controller: _searchController,
                        decoration: InputDecoration(
                          hintText: '輸入食物名稱（如：雞胸肉、白飯）',
                          filled: true,
                          fillColor: Colors.white,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                        ),
                        onSubmitted: (_) => _search(),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: _gramsController,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText: '克數',
                          filled: true,
                          fillColor: Colors.white,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 12,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: _isLoading ? null : _search,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green.shade700,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 14,
                        ),
                      ),
                      child: _isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text('搜尋'),
                    ),
                  ],
                ),
                if (_stats != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      '資料來源：台灣食品營養成分資料庫 2024 (${_stats!.totalCategories} 分類)',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // 錯誤訊息
          if (_errorMessage != null)
            Container(
              width: double.infinity,
              color: Colors.red.shade50,
              padding: const EdgeInsets.all(12),
              child: Text(
                _errorMessage!,
                style: TextStyle(color: Colors.red.shade700),
              ),
            ),

          // 計算結果（如果有）
          if (_calculatedResult != null) _buildCalculatedResult(),

          // 搜尋結果列表
          Expanded(
            child: _searchResults.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    itemCount: _searchResults.length,
                    itemBuilder: (context, index) {
                      return _buildFoodCard(_searchResults[index]);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.search,
            size: 64,
            color: Colors.grey.shade400,
          ),
          const SizedBox(height: 16),
          Text(
            '輸入食物名稱開始查詢',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '例如：白飯、雞胸肉、菠菜、蘋果',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFoodCard(FoodNutrition food) {
    final n = food.per100g;
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: () => _calculate(food.name),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      food.name,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.green.shade100,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      food.category,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.green.shade700,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                '每 100g 營養成分：',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildNutrientBadge('熱量', '${n.calories.toStringAsFixed(0)} kcal', Colors.orange),
                  _buildNutrientBadge('蛋白質', '${n.protein.toStringAsFixed(1)} g', Colors.red),
                  _buildNutrientBadge('碳水', '${n.carbs.toStringAsFixed(1)} g', Colors.blue),
                  _buildNutrientBadge('脂肪', '${n.fat.toStringAsFixed(1)} g', Colors.purple),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildNutrientBadge('鈉', '${n.sodium.toStringAsFixed(0)} mg', Colors.teal),
                  _buildNutrientBadge('鉀', '${n.potassium.toStringAsFixed(0)} mg', Colors.indigo),
                  _buildNutrientBadge('纖維', '${n.fiber.toStringAsFixed(1)} g', Colors.brown),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '點擊計算指定克數的營養',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey.shade500,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNutrientBadge(String label, String value, Color color) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(vertical: 6),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Column(
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                color: color.withValues(alpha: 0.8),
              ),
            ),
            Text(
              value,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCalculatedResult() {
    final r = _calculatedResult!;
    final n = r.nutrients;

    return Container(
      width: double.infinity,
      color: Colors.blue.shade50,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.calculate, color: Colors.blue),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '${r.name} ${r.grams.toStringAsFixed(0)}g 營養計算',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close, size: 20),
                onPressed: () => setState(() => _calculatedResult = null),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _buildCalculatedChip('🔥 熱量', '${n.calories.toStringAsFixed(0)} kcal'),
              _buildCalculatedChip('💪 蛋白質', '${n.protein.toStringAsFixed(1)} g'),
              _buildCalculatedChip('🍞 碳水', '${n.carbs.toStringAsFixed(1)} g'),
              _buildCalculatedChip('🧈 脂肪', '${n.fat.toStringAsFixed(1)} g'),
              _buildCalculatedChip('🧂 鈉', '${n.sodium.toStringAsFixed(0)} mg'),
              _buildCalculatedChip('🥬 鉀', '${n.potassium.toStringAsFixed(0)} mg'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCalculatedChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 4,
          ),
        ],
      ),
      child: Text(
        '$label $value',
        style: const TextStyle(fontSize: 13),
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    _gramsController.dispose();
    super.dispose();
  }
}
