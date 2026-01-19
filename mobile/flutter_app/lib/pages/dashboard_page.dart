import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:shimmer/shimmer.dart';
import 'dart:math' show pi;
import '../state/app_state.dart';
import '../services/user_service.dart';
import 'report_detail_page.dart';

class DashboardPage extends ConsumerStatefulWidget {
  const DashboardPage({super.key});

  @override
  ConsumerState<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends ConsumerState<DashboardPage> {
  final UserService _userService = UserService();

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    ref.read(dashboardLoadingProvider.notifier).state = true;
    ref.read(dashboardErrorProvider.notifier).state = null;

    try {
      final data = await _userService.getMyDashboard();
      ref.read(dashboardProvider.notifier).state = data;
    } catch (e) {
      ref.read(dashboardErrorProvider.notifier).state = e.toString();
    } finally {
      ref.read(dashboardLoadingProvider.notifier).state = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final dashboard = ref.watch(dashboardProvider);
    final isLoading = ref.watch(dashboardLoadingProvider);
    final error = ref.watch(dashboardErrorProvider);
    final memoryReport = ref.watch(reportProvider);
    // 優先使用記憶體中的報告，沒有則使用 API 回傳的持久化報告
    final report = memoryReport ?? dashboard?.aiReport;

    // 還在載入 - 顯示骨架屏
    if (isLoading) {
      return _buildShimmerLoading();
    }

    // 有錯誤（未登入或未設定 Profile）
    if (error != null) {
      return _buildErrorState(error);
    }

    // 沒有資料
    if (dashboard == null) {
      return _buildEmptyState();
    }

    final score = dashboard.healthScore ?? 0;
    final history = dashboard.history
        .map((h) => {
              'created_at': h.createdAt,
              'health_score': h.healthScore,
            })
        .toList();
    final abnormalItems = dashboard.abnormalItems
        .map((a) => {
              'name': a.name,
              'value': a.value,
              'unit': a.unit,
              'severity': a.severity,
              'normal_range': a.normalRange,
            })
        .toList();
    final keyMetrics = dashboard.keyMetrics;

    return RefreshIndicator(
      onRefresh: _loadDashboard,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 健康評分 - 重新設計
          _buildHealthScoreCard(score),
          const SizedBox(height: 24),

          // 異常指標 - 移到前面，更重要
          const Text('需要注意的指標',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildAbnormalList(abnormalItems),
          const SizedBox(height: 24),

          // 趨勢圖表
          const Text('健康評分趨勢',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildHistoryChart(history),
          const SizedBox(height: 24),

          // 關鍵指標卡片
          const Text('關鍵健康指標',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildKeyMetricsGrid(context, keyMetrics),
          const SizedBox(height: 24),

          // AI 建議區（整合）
          const Text('AI 健康建議',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildAdviceCard(
              context, report, 'food_advice', '尚無飲食建議', Icons.restaurant, '飲食建議'),
          const SizedBox(height: 12),
          _buildAdviceCard(context, report, 'supplement_advice', '尚無保健建議',
              Icons.medical_services, '保健建議'),
          const SizedBox(height: 12),
          _buildMealPlanCard(context, report),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.orange[400]),
            const SizedBox(height: 16),
            Text(
              error.contains('登入') ? '尚未登入' : '無法載入 Dashboard',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              error.replaceAll('Exception: ', ''),
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _loadDashboard,
              icon: const Icon(Icons.refresh),
              label: const Text('重試'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 空白狀態插圖
            Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.monitor_heart_outlined,
                size: 100,
                color: Colors.green.shade300,
              ),
            ),
            const SizedBox(height: 32),
            const Text(
              '開始您的健康之旅',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Color(0xFF6B8E23),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              '上傳您的健檢報告\n讓 AI 為您分析健康狀況',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
                height: 1.5,
              ),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.check_circle, color: Colors.green.shade400, size: 20),
                const SizedBox(width: 8),
                const Text('個人化健康建議'),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.check_circle, color: Colors.green.shade400, size: 20),
                const SizedBox(width: 8),
                const Text('智能營養追蹤'),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.check_circle, color: Colors.green.shade400, size: 20),
                const SizedBox(width: 8),
                const Text('AI 健康教練'),
              ],
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: _loadDashboard,
              icon: const Icon(Icons.refresh),
              label: const Text('重新載入'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 骨架屏 Loading 效果
  Widget _buildShimmerLoading() {
    return Shimmer.fromColors(
      baseColor: Colors.grey[300]!,
      highlightColor: Colors.grey[100]!,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 健康評分骨架
          Card(
            elevation: 4,
            child: Container(
              height: 168,
              padding: const EdgeInsets.all(24),
              child: Row(
                children: [
                  Container(
                    width: 120,
                    height: 120,
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 24),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: double.infinity,
                          height: 16,
                          color: Colors.white,
                        ),
                        const SizedBox(height: 12),
                        Container(
                          width: 120,
                          height: 32,
                          color: Colors.white,
                        ),
                        const SizedBox(height: 12),
                        Container(
                          width: 200,
                          height: 14,
                          color: Colors.white,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // 異常指標骨架
          Container(
            height: 18,
            width: 120,
            color: Colors.white,
          ),
          const SizedBox(height: 12),
          ...List.generate(
            2,
            (index) => Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Container(
                height: 80,
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: double.infinity,
                            height: 16,
                            color: Colors.white,
                          ),
                          const SizedBox(height: 8),
                          Container(
                            width: 150,
                            height: 14,
                            color: Colors.white,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // 趨勢圖表骨架
          Container(
            height: 18,
            width: 100,
            color: Colors.white,
          ),
          const SizedBox(height: 12),
          Card(
            child: Container(
              height: 240,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 24),

          // 關鍵指標骨架
          Container(
            height: 18,
            width: 100,
            color: Colors.white,
          ),
          const SizedBox(height: 12),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.5,
            children: List.generate(
              4,
              (index) => Card(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 60,
                        height: 14,
                        color: Colors.white,
                      ),
                      const SizedBox(height: 8),
                      Container(
                        width: 80,
                        height: 24,
                        color: Colors.white,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // 新增：健康評分卡片（帶環形進度）
  Widget _buildHealthScoreCard(int score) {
    final grading = _getScoreGrading(score);
    
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Row(
          children: [
            // 環形進度
            SizedBox(
              width: 120,
              height: 120,
              child: CustomPaint(
                painter: _CircularScorePainter(
                  score: score,
                  color: grading['color'] as Color,
                ),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '$score',
                        style: TextStyle(
                          fontSize: 36,
                          fontWeight: FontWeight.bold,
                          color: grading['color'] as Color,
                        ),
                      ),
                      Text(
                        '/ 100',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 24),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '健康綜合評分',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(
                        grading['icon'] as IconData,
                        color: grading['color'] as Color,
                        size: 28,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        grading['label'] as String,
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: grading['color'] as Color,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    grading['message'] as String,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // 評分等級系統
  Map<String, dynamic> _getScoreGrading(int score) {
    if (score >= 85) {
      return {
        'label': '優秀',
        'color': Colors.green,
        'icon': Icons.emoji_events,
        'message': '健康狀況非常良好，請繼續保持！'
      };
    } else if (score >= 70) {
      return {
        'label': '良好',
        'color': Colors.lightGreen,
        'icon': Icons.thumb_up,
        'message': '健康狀況不錯，可以做得更好。'
      };
    } else if (score >= 50) {
      return {
        'label': '普通',
        'color': Colors.orange,
        'icon': Icons.warning_amber,
        'message': '有些指標需要注意，建議改善生活習慣。'
      };
    } else {
      return {
        'label': '需改善',
        'color': Colors.red,
        'icon': Icons.error_outline,
        'message': '多項指標異常，請盡快諮詢醫療專業人員。'
      };
    }
  }

  // 關鍵指標網格
  Widget _buildKeyMetricsGrid(BuildContext context, List<DashboardKeyMetric> metrics) {
    if (metrics.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: Column(
              children: [
                Icon(Icons.analytics_outlined, size: 48, color: Colors.grey[400]),
                const SizedBox(height: 12),
                Text(
                  '尚無關鍵指標',
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.5,
      children: metrics.map((m) => _buildMetricCard({
        'label': m.label,
        'value': m.value?.toString() ?? '-',
        'unit': m.unit ?? '',
        'status': m.status,
      })).toList(),
    );
  }

  Widget _buildMetricCard(Map<String, String> metric) {
    Color statusColor;
    switch (metric['status']) {
      case 'danger':
        statusColor = Colors.red;
        break;
      case 'warning':
        statusColor = Colors.orange;
        break;
      case 'caution':
        statusColor = Colors.amber;
        break;
      default:
        statusColor = Colors.green;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              metric['label']!,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[700],
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  metric['value']!,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: statusColor,
                  ),
                ),
                if (metric['unit']!.isNotEmpty) ...[
                  const SizedBox(width: 4),
                  Text(
                    metric['unit']!,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryChart(List<dynamic> history) {
    if (history.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(48),
          child: Column(
            children: [
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.trending_up,
                  size: 50,
                  color: Colors.blue.shade300,
                ),
              ),
              const SizedBox(height: 20),
              Text(
                '尚無趨勢數據',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey[800],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '上傳多次健檢報告後\n即可看到健康趨勢變化',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[600],
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      );
    }

    final spots = <FlSpot>[];
    final dates = <String>[];
    for (int i = 0; i < history.length; i++) {
      final item = history[i] as Map<String, dynamic>;
      final score = (item['health_score'] as num?)?.toDouble() ?? 0.0;
      spots.add(FlSpot(i.toDouble(), score));
      
      // 提取日期標籤（只顯示月/日）
      final dateStr = item['created_at'] as String;
      if (dateStr.length >= 10) {
        dates.add('${dateStr.substring(5, 7)}/${dateStr.substring(8, 10)}');
      } else {
        dates.add('');
      }
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          height: 240,
          child: LineChart(
            LineChartData(
              gridData: FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: 20,
                getDrawingHorizontalLine: (value) {
                  return FlLine(
                    color: Colors.grey[300]!,
                    strokeWidth: 1,
                  );
                },
              ),
              titlesData: FlTitlesData(
                show: true,
                rightTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                topTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 30,
                    interval: 1,
                    getTitlesWidget: (value, meta) {
                      final index = value.toInt();
                      if (index >= 0 && index < dates.length) {
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            dates[index],
                            style: const TextStyle(
                              color: Colors.grey,
                              fontSize: 11,
                            ),
                          ),
                        );
                      }
                      return const Text('');
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 40,
                    interval: 20,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '${value.toInt()}',
                        style: const TextStyle(
                          color: Colors.grey,
                          fontSize: 12,
                        ),
                      );
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(
                show: true,
                border: Border(
                  bottom: BorderSide(color: Colors.grey[300]!),
                  left: BorderSide(color: Colors.grey[300]!),
                ),
              ),
              minX: 0,
              maxX: (spots.length - 1).toDouble(),
              minY: 0,
              maxY: 100,
              lineTouchData: LineTouchData(
                touchTooltipData: LineTouchTooltipData(
                  getTooltipItems: (List<LineBarSpot> touchedBarSpots) {
                    return touchedBarSpots.map((barSpot) {
                      return LineTooltipItem(
                        '評分: ${barSpot.y.toInt()}',
                        const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      );
                    }).toList();
                  },
                ),
              ),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  color: Colors.blue,
                  barWidth: 3,
                  isStrokeCapRound: true,
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, percent, barData, index) {
                      return FlDotCirclePainter(
                        radius: 4,
                        color: Colors.white,
                        strokeWidth: 2,
                        strokeColor: Colors.blue,
                      );
                    },
                  ),
                  belowBarData: BarAreaData(
                    show: true,
                    color: Colors.blue.withOpacity(0.1),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSummaryCard(Map<String, dynamic>? report) {
    if (report == null) {
      return const Text('尚未產生報告，請先完成上傳分析。');
    }

    final foodAdvice = (report['food_advice'] as List<dynamic>?)?.isNotEmpty == true
        ? report['food_advice'][0]['content'] as String? ?? ''
        : '';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(
          foodAdvice.isNotEmpty ? foodAdvice : 'AI 建議摘要尚未生成。',
          maxLines: 6,
          overflow: TextOverflow.ellipsis,
        ),
      ),
    );
  }

  Widget _buildAbnormalList(List<dynamic> abnormalItems) {
    if (abnormalItems.isEmpty) {
      return Card(
        elevation: 2,
        color: Colors.green[50],
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            children: [
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: Colors.green[100],
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.celebration_outlined,
                  color: Colors.green[700],
                  size: 40,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                '太棒了！',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.green[800],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '所有檢測數值都在正常範圍內',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15,
                  color: Colors.green[700],
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '請繼續保持健康的生活習慣',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.green[600],
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: abnormalItems.map((item) {
        final itemMap = item as Map<String, dynamic>;
        final name = itemMap['name']?.toString() ?? 'Unknown';
        final value = itemMap['value'];
        final unit = itemMap['unit']?.toString() ?? '';
        final severity = itemMap['severity']?.toString() ?? 'caution';
        final normalRange = itemMap['normal_range']?.toString() ?? '';

        Color bgColor, iconColor, textColor;
        IconData icon;
        String severityText;

        switch (severity) {
          case 'danger':
            bgColor = Colors.red[50]!;
            iconColor = Colors.red[600]!;
            textColor = Colors.red[800]!;
            icon = Icons.dangerous;
            severityText = '危險';
            break;
          case 'warning':
            bgColor = Colors.orange[50]!;
            iconColor = Colors.orange[600]!;
            textColor = Colors.orange[800]!;
            icon = Icons.warning_amber;
            severityText = '警告';
            break;
          default: // caution
            bgColor = Colors.amber[50]!;
            iconColor = Colors.amber[700]!;
            textColor = Colors.amber[900]!;
            icon = Icons.info_outline;
            severityText = '注意';
        }

        return Card(
          color: bgColor,
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(icon, color: iconColor, size: 32),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            name,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: textColor,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: iconColor.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              severityText,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: textColor,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Text(
                            '檢測值：',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[700],
                            ),
                          ),
                          Text(
                            '$value $unit',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: textColor,
                            ),
                          ),
                          if (normalRange.isNotEmpty) ...[
                            const SizedBox(width: 16),
                            Text(
                              '正常值：',
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey[600],
                              ),
                            ),
                            Text(
                              normalRange,
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey[700],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildAdviceCard(BuildContext context, Map<String, dynamic>? report, String key, String emptyText, IconData icon, String cardTitle) {
    final list = report?[key] as List<dynamic>?;
    if (list == null || list.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: Column(
              children: [
                Icon(icon, size: 48, color: Colors.grey[400]),
                const SizedBox(height: 12),
                Text(
                  emptyText,
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // 從報告中取得建議內容
    final firstItem = list[0] as Map<String, dynamic>;
    final title = firstItem['title'] as String? ?? cardTitle;
    final content = firstItem['content'] as String? ?? '';
    final actionItems = (firstItem['action_items'] as List<dynamic>?)?.map((e) => e.toString()).toList();
    
    final wordCount = content.length;
    final preview = content.length > 200 ? '${content.substring(0, 200)}...' : content;
    
    return Card(
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ReportDetailPage(
                title: title,
                content: content,
                actionItems: actionItems,
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(icon, size: 20, color: Theme.of(context).primaryColor),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      title,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                  Text(
                    '$wordCount 字',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  const SizedBox(width: 8),
                  const Icon(Icons.arrow_forward_ios, size: 16),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                preview,
                style: const TextStyle(fontSize: 14, height: 1.5),
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              Text(
                '點擊查看完整內容 →',
                style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).primaryColor,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMealPlanCard(BuildContext context, Map<String, dynamic>? report) {
    if (report == null) {
      return const Text('尚無餐飲計劃');
    }
    
    final mealPlan = report['meal_plan'] as Map<String, dynamic>?;
    if (mealPlan == null || mealPlan.isEmpty) {
      return const Text('尚無餐飲計劃');
    }
    
    final markdownContent = mealPlan['markdown_content'] as String? ?? '';
    if (markdownContent.isEmpty) {
      return const Text('尚無餐飲計劃');
    }
    
    final wordCount = markdownContent.length;
    final preview = markdownContent.length > 200 ? '${markdownContent.substring(0, 200)}...' : markdownContent;
    
    return Card(
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ReportDetailPage(
                title: '7天餐飲計劃',
                content: markdownContent,
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.calendar_month, size: 20, color: Theme.of(context).primaryColor),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      '專屬餐飲計劃',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                  Text(
                    '$wordCount 字',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  const SizedBox(width: 8),
                  const Icon(Icons.arrow_forward_ios, size: 16),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                preview,
                style: const TextStyle(fontSize: 14, height: 1.5),
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              Text(
                '點擊查看完整 7 天計劃 →',
                style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).primaryColor,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// 環形進度繪製器
class _CircularScorePainter extends CustomPainter {
  final int score;
  final Color color;

  _CircularScorePainter({required this.score, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 8;
    
    // 背景圓環
    final bgPaint = Paint()
      ..color = Colors.grey[200]!
      ..style = PaintingStyle.stroke
      ..strokeWidth = 12
      ..strokeCap = StrokeCap.round;
    
    canvas.drawCircle(center, radius, bgPaint);
    
    // 進度圓環
    final progressPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 12
      ..strokeCap = StrokeCap.round;
    
    final sweepAngle = 2 * pi * (score / 100);
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -pi / 2, // 從頂部開始
      sweepAngle,
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(_CircularScorePainter oldDelegate) {
    return oldDelegate.score != score || oldDelegate.color != color;
  }
}
