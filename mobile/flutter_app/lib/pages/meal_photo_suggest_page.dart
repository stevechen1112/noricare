import 'dart:typed_data' show Uint8List;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/food_vision.dart';
import '../models/meal.dart';
import '../services/meal_service.dart';
import 'upload_page_io.dart' if (dart.library.html) 'upload_page_web.dart' as platform;

class MealPhotoSuggestPage extends StatefulWidget {
  const MealPhotoSuggestPage({super.key});

  @override
  State<MealPhotoSuggestPage> createState() => _MealPhotoSuggestPageState();
}

class _MealPhotoSuggestPageState extends State<MealPhotoSuggestPage> {
  final MealService _service = MealService();
  final ImagePicker _picker = ImagePicker();

  XFile? _image;
  bool _loading = false;
  List<FoodVisionSuggestItem> _items = [];

  final Map<int, double> _gramsByIndex = {};
  final List<MealItemDraft> _selected = [];

  Future<void> _pickImage(ImageSource source) async {
    final xfile = await _picker.pickImage(source: source, imageQuality: 85);
    if (xfile == null) return;
    setState(() {
      _image = xfile;
      _items = [];
      _gramsByIndex.clear();
      _selected.clear();
    });
  }

  Future<void> _analyze() async {
    if (_image == null) return;
    setState(() => _loading = true);
    try {
      final res = await _service.suggestFoodFromPhoto(
        _image!,
        limit: 5,
        profile: 'bento',
      );
      setState(() {
        _items = res.items;
        _gramsByIndex.clear();
        for (var i = 0; i < _items.length; i++) {
          _gramsByIndex[i] = _items[i].estimatedGrams;
        }
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('照片分析失敗：$e')),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _addItem(int index) {
    final item = _items[index];
    final foodId = item.matchedFoodId;
    if (foodId == null || foodId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('此候選尚未對齊到資料庫，請改用手動對齊。')),
      );
      return;
    }

    final grams = (_gramsByIndex[index] ?? item.estimatedGrams).clamp(1, 2000).toDouble();
    final foodName = (item.matchedName?.isNotEmpty ?? false) ? item.matchedName! : item.name;

    setState(() {
      _selected.add(MealItemDraft(foodId: foodId, foodName: foodName, grams: grams));
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('已加入：$foodName（${grams.toStringAsFixed(0)}g）')),
    );
  }

  Widget _buildImagePreview() {
    if (_image == null) return const SizedBox.shrink();
    
    if (kIsWeb) {
      return FutureBuilder<Uint8List>(
        future: _image!.readAsBytes(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return Image.memory(
              snapshot.data!,
              height: 220,
              fit: BoxFit.cover,
            );
          }
          return const SizedBox(
            height: 220,
            child: Center(child: CircularProgressIndicator()),
          );
        },
      );
    }
    
    // For non-web platforms
    return platform.buildFileImagePreview(_image!.path);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('拍照辨識（粗估份量）'),
        actions: [
          TextButton(
            onPressed: _selected.isEmpty
                ? null
                : () => Navigator.of(context).pop<List<MealItemDraft>>(_selected),
            child: Text('加入（${_selected.length}）'),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _loading ? null : () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('拍照'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _loading ? null : () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('相簿'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_image != null) ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: _buildImagePreview(),
            ),
            const SizedBox(height: 12),
          ],
          ElevatedButton.icon(
            onPressed: (_image == null || _loading) ? null : _analyze,
            icon: _loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.search),
            label: Text(_loading ? '分析中...' : '分析照片'),
          ),
          const SizedBox(height: 16),
          if (_items.isEmpty)
            const Text('提示：分析後會顯示候選食物，點「小/中/大」可快速選份量。')
          else ...[
            const Text('候選食物', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ...List.generate(_items.length, (idx) {
              final item = _items[idx];
              final name = (item.matchedName?.isNotEmpty ?? false) ? item.matchedName! : item.name;
              final category = item.matchedCategory ?? '未知';
              final minG = item.gramsMin;
              final maxG = item.gramsMax;
              final midG = item.estimatedGrams;
              final grams = _gramsByIndex[idx] ?? midG;
              final canAdd = (item.matchedFoodId?.isNotEmpty ?? false);

              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(name, style: const TextStyle(fontWeight: FontWeight.bold)),
                                const SizedBox(height: 4),
                                Text('分類：$category｜估計範圍：${minG.toStringAsFixed(0)}–${maxG.toStringAsFixed(0)} g'),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: canAdd ? () => _addItem(idx) : null,
                            child: const Text('加入'),
                          ),
                        ],
                      ),
                      if (!canAdd) ...[
                        const SizedBox(height: 6),
                        const Text('需手動對齊', style: TextStyle(color: Colors.grey)),
                      ],
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () => setState(() => _gramsByIndex[idx] = minG),
                              child: const Text('小'),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () => setState(() => _gramsByIndex[idx] = midG),
                              child: const Text('中'),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () => setState(() => _gramsByIndex[idx] = maxG),
                              child: const Text('大'),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          const Text('份量：'),
                          Text('${grams.toStringAsFixed(0)} g'),
                        ],
                      ),
                      Slider(
                        value: grams.clamp(minG, maxG),
                        min: minG,
                        max: maxG,
                        divisions: (maxG - minG) >= 10 ? ((maxG - minG) / 10).round() : null,
                        label: '${grams.toStringAsFixed(0)} g',
                        onChanged: (v) => setState(() => _gramsByIndex[idx] = v),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ],
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: ElevatedButton(
            onPressed: _selected.isEmpty
                ? null
                : () => Navigator.of(context).pop<List<MealItemDraft>>(_selected),
            child: Text('加入到餐點（${_selected.length}）'),
          ),
        ),
      ),
    );
  }
}
