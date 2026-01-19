import 'dart:typed_data' show Uint8List;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../services/report_service.dart';
import '../state/app_state.dart';
import 'upload_page_io.dart' if (dart.library.html) 'upload_page_web.dart' as platform;

/// 常見健檢指標的標準參考範圍（用於判斷異常）
const Map<String, Map<String, dynamic>> _referenceRanges = {
  // 血糖相關
  'GLUCOSE': {'min': 70, 'max': 99, 'unit': 'mg/dL'},
  'Glucose': {'min': 70, 'max': 99, 'unit': 'mg/dL'},
  '空腹血糖': {'min': 70, 'max': 99, 'unit': 'mg/dL'},
  'Glucose (Post-prandial)': {'max': 140, 'unit': 'mg/dL'},
  '飯後血糖': {'max': 140, 'unit': 'mg/dL'},
  '飯後血糖 (Glucose)': {'max': 140, 'unit': 'mg/dL'},
  '飯後血糖 (Glucose PC)': {'max': 140, 'unit': 'mg/dL'},
  'Glucose_PC': {'max': 140, 'unit': 'mg/dL'},
  'HbA1c': {'min': 4.0, 'max': 5.6, 'unit': '%'},
  '醣化血色素': {'min': 4.0, 'max': 5.6, 'unit': '%'},
  '醣化血色素 (HbA1c)': {'min': 4.0, 'max': 5.6, 'unit': '%'},
  
  // 腎功能
  'Creatinine': {'min': 0.7, 'max': 1.2, 'unit': 'mg/dL'},
  'CRE(肌酸酐)': {'min': 0.7, 'max': 1.2, 'unit': 'mg/dL'},
  '肌酸酐': {'min': 0.7, 'max': 1.2, 'unit': 'mg/dL'},
  'eGFR': {'min': 60, 'unit': 'mL/min/1.73m²'},
  'BUN': {'min': 7, 'max': 20, 'unit': 'mg/dL'},
  
  // 肝功能
  'AST': {'max': 40, 'unit': 'U/L'},
  'AST (GOT)': {'max': 40, 'unit': 'U/L'},
  'GOT': {'max': 40, 'unit': 'U/L'},
  'ALT': {'max': 40, 'unit': 'U/L'},
  'ALT (GPT)': {'max': 40, 'unit': 'U/L'},
  'GPT': {'max': 40, 'unit': 'U/L'},
  
  // 血脂
  'Cholesterol': {'max': 200, 'unit': 'mg/dL'},
  '總膽固醇': {'max': 200, 'unit': 'mg/dL'},
  'Triglyceride': {'max': 150, 'unit': 'mg/dL'},
  '三酸甘油酯': {'max': 150, 'unit': 'mg/dL'},
  'LDL': {'max': 130, 'unit': 'mg/dL'},
  'HDL': {'min': 40, 'unit': 'mg/dL'},
  
  // 血壓
  'Systolic_BP': {'max': 120, 'unit': 'mmHg'},
  '收縮壓': {'max': 120, 'unit': 'mmHg'},
  'Diastolic_BP': {'max': 80, 'unit': 'mmHg'},
  '舒張壓': {'max': 80, 'unit': 'mmHg'},
  
  // 其他
  'BMI': {'min': 18.5, 'max': 24, 'unit': 'kg/m²'},
  'Hb': {'min': 13.5, 'max': 17.5, 'unit': 'g/dL'},
  '血紅素': {'min': 13.5, 'max': 17.5, 'unit': 'g/dL'},
};

/// 根據數值和參考範圍判斷狀態
String _determineStatus(dynamic value, String refRangeStr, String fieldName) {
  if (value == null) return 'Normal';
  
  double numValue;
  if (value is num) {
    numValue = value.toDouble();
  } else {
    return 'Normal';
  }
  
  // 優先使用內建的參考範圍
  final builtInRef = _referenceRanges[fieldName];
  if (builtInRef != null) {
    final min = builtInRef['min'] as num?;
    final max = builtInRef['max'] as num?;
    
    if (max != null && numValue > max) return 'High';
    if (min != null && numValue < min) return 'Low';
    return 'Normal';
  }
  
  // 如果沒有內建範圍，嘗試解析 OCR 返回的參考範圍
  if (refRangeStr.isEmpty) return 'Normal';
  
  // 處理 "< 140" 格式
  if (refRangeStr.startsWith('<')) {
    final maxStr = refRangeStr.replaceAll('<', '').replaceAll(' ', '');
    final max = double.tryParse(maxStr);
    if (max != null && numValue > max) return 'High';
    return 'Normal';
  }
  
  // 處理 "> 60" 格式
  if (refRangeStr.startsWith('>')) {
    final minStr = refRangeStr.replaceAll('>', '').replaceAll(' ', '');
    final min = double.tryParse(minStr);
    if (min != null && numValue < min) return 'Low';
    return 'Normal';
  }
  
  // 處理 "70-99" 或 "4.0 - 5.6" 格式
  final rangeParts = refRangeStr.split(RegExp(r'[-–~]'));
  if (rangeParts.length == 2) {
    final min = double.tryParse(rangeParts[0].trim());
    final max = double.tryParse(rangeParts[1].trim());
    if (min != null && numValue < min) return 'Low';
    if (max != null && numValue > max) return 'High';
  }
  
  return 'Normal';
}

class UploadPage extends ConsumerStatefulWidget {
  const UploadPage({super.key});

  @override
  ConsumerState<UploadPage> createState() => _UploadPageState();
}

class _UploadPageState extends ConsumerState<UploadPage> {
  final List<XFile> _selectedFiles = [];
  bool _loading = false;
  String _statusText = '';

  @override
  Widget build(BuildContext context) {
    final userProfile = ref.watch(userProfileProvider);

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('上傳健檢報告', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Text('支援多張 JPG / PNG 檔案 (已選 ${_selectedFiles.length} 張)'),
          const SizedBox(height: 12),
          if (userProfile == null)
            const Text('⚠️ 請先在個人資料頁完成檔案建立。', style: TextStyle(color: Colors.red)),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _loading ? null : _pickMultipleImages,
                  icon: const Icon(Icons.photo_library),
                  label: const Text('選擇多張'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _loading ? null : _takePhoto,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('拍照'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          
          // 顯示已選圖片的縮圖
          if (_selectedFiles.isNotEmpty) ...[
            SizedBox(
              height: 120,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _selectedFiles.length,
                itemBuilder: (context, index) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 8.0),
                    child: Stack(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: _buildImagePreview(_selectedFiles[index]),
                        ),
                        // 刪除按鈕
                        Positioned(
                          top: 4,
                          right: 4,
                          child: GestureDetector(
                            onTap: () => _removeImage(index),
                            child: Container(
                              decoration: const BoxDecoration(
                                color: Colors.red,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.close,
                                color: Colors.white,
                                size: 20,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 12),
          ],
          
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: _loading ? null : _startAnalysis,
                  child: _loading 
                    ? const CircularProgressIndicator() 
                    : Text('開始分析 (${_selectedFiles.length} 張)'),
                ),
              ),
              if (_selectedFiles.isNotEmpty) ...[
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _loading ? null : _clearAll,
                  icon: const Icon(Icons.delete_outline),
                  tooltip: '清空全部',
                ),
              ],
            ],
          ),
          if (_statusText.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(_statusText),
          ],
        ],
      ),
    );
  }

  Future<void> _pickMultipleImages() async {
    final picker = ImagePicker();
    final List<XFile> picked = await picker.pickMultiImage();
    if (picked.isNotEmpty) {
      setState(() {
        _selectedFiles.addAll(picked);
      });
    }
  }

  Future<void> _takePhoto() async {
    final picker = ImagePicker();
    final XFile? picked = await picker.pickImage(source: ImageSource.camera);
    if (picked != null) {
      setState(() => _selectedFiles.add(picked));
    }
  }

  /// 移除單張圖片
  void _removeImage(int index) {
    setState(() {
      _selectedFiles.removeAt(index);
    });
  }

  /// 清空所有圖片
  void _clearAll() {
    setState(() {
      _selectedFiles.clear();
    });
  }

  /// 建立圖片預覽 Widget
  Widget _buildImagePreview(XFile file) {
    if (kIsWeb) {
      return FutureBuilder<Uint8List>(
        future: file.readAsBytes(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return Image.memory(
              snapshot.data!,
              width: 120,
              height: 120,
              fit: BoxFit.cover,
            );
          }
          return Container(
            width: 120,
            height: 120,
            color: Colors.grey[300],
            child: const Center(child: CircularProgressIndicator()),
          );
        },
      );
    } else {
      // 移動端：直接使用 platform 條件導入的 buildFileImagePreview
      return platform.buildFileImagePreview(file.path);
    }
  }

  Future<void> _startAnalysis() async {
    final userProfile = ref.read(userProfileProvider);
    if (userProfile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請先建立使用者資料')),
      );
      return;
    }

    if (_selectedFiles.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請先選擇至少一張圖片')),
      );
      return;
    }

    setState(() {
      _loading = true;
      _statusText = '正在上傳並解析 ${_selectedFiles.length} 張圖片...';
    });

    try {
      final reportService = ReportService();
      Map<String, dynamic> combinedStructuredData = {};
      List<dynamic> allAbnormalItems = [];

      // 逐一處理每張圖片
      for (int fileIndex = 0; fileIndex < _selectedFiles.length; fileIndex++) {
        setState(() => _statusText = '正在處理第 ${fileIndex + 1}/${_selectedFiles.length} 張圖片...');
        
        final file = _selectedFiles[fileIndex];
        final fileId = await reportService.uploadOcr(file);

        Map<String, dynamic>? ocrResult;
        for (int i = 0; i < 10; i++) {
          await Future.delayed(const Duration(seconds: 2));
          final status = await reportService.getOcrResult(fileId);
          if (status['status'] == 'completed') {
            final data = status['data'];
            // 處理後端返回的格式
            if (data is Map<String, dynamic>) {
              ocrResult = data;
            } else {
              throw Exception('OCR 結果格式錯誤');
            }
            break;
          }
          if (status['status'] == 'failed') {
            throw Exception('第 ${fileIndex + 1} 張圖片 OCR 解析失敗');
          }
          setState(() => _statusText = '正在分析第 ${fileIndex + 1}/${_selectedFiles.length} 張...');
        }

        if (ocrResult == null) {
          throw Exception('第 ${fileIndex + 1} 張圖片 OCR 解析超時');
        }

        // 從後端格式中提取數據：data.structured_data (而非 data.fields)
        final fields = (ocrResult['structured_data'] ?? {}) as Map<String, dynamic>;
        
        // 將 fields 格式轉換為後端期望的格式
        // 從 {"Glucose": {"value": 117, "unit": "mg/dL", ...}} 
        // 保持完整的物件結構
        for (var entry in fields.entries) {
          final fieldName = entry.key;
          final fieldData = entry.value as Map<String, dynamic>;
          final value = fieldData['value'];
          final refRange = (fieldData['reference_range'] ?? '').toString();
          
          // 根據參考範圍和內建標準判斷狀態
          String status = _determineStatus(value, refRange, fieldName);
          
          combinedStructuredData[fieldName] = {
            'value': fieldData['value'],
            'unit': fieldData['unit'] ?? '',
            'reference_range': refRange,
            'status': status,
          };
          
          // 如果是異常值，加入異常清單（帶數值說明）
          if (status == 'High' || status == 'Low') {
            final unit = fieldData['unit'] ?? '';
            final statusText = status == 'High' ? '偏高' : '偏低';
            allAbnormalItems.add('$fieldName: $value $unit ($statusText)');
          }
        }
      }

      // 更新狀態
      ref.read(healthDataProvider.notifier).state = combinedStructuredData;
      ref.read(abnormalItemsProvider.notifier).state = allAbnormalItems;

      final payload = {
        'user_profile': userProfile,
        'health_data': combinedStructuredData,
        'abnormal_items': allAbnormalItems,
      };

      setState(() => _statusText = '正在生成 AI 綜合報告...');
      final report = await reportService.generateReport(payload);
      ref.read(reportProvider.notifier).state = report;

      final userId = userProfile['id'] as String;
      final historyResp = await reportService.fetchHistory(userId);
      ref.read(historyProvider.notifier).state = (historyResp['history'] ?? []) as List<dynamic>;

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ ${_selectedFiles.length} 張圖片分析完成，請查看 Dashboard'),
            duration: const Duration(seconds: 5),
            action: SnackBarAction(
              label: '清空圖片',
              onPressed: () => setState(() => _selectedFiles.clear()),
            ),
          ),
        );
        // 不自動清空圖片，讓用戶可以查看已上傳的內容
        // 用戶可以手動點擊垃圾桶圖示清空
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('分析失敗：$e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _statusText = '';
        });
      }
    }
  }
}
