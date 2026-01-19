import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class ReportDetailPage extends StatelessWidget {
  final String title;
  final String content;
  final List<String>? actionItems;

  const ReportDetailPage({
    super.key,
    required this.title,
    required this.content,
    this.actionItems,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Markdown 內容顯示
          MarkdownBody(
            data: content,
            styleSheet: MarkdownStyleSheet(
              h1: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              h2: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              h3: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              p: const TextStyle(fontSize: 16, height: 1.6),
              listBullet: const TextStyle(fontSize: 16),
            ),
          ),
          
          // 行動項目
          if (actionItems != null && actionItems!.isNotEmpty) ...[
            const SizedBox(height: 24),
            const Divider(),
            const SizedBox(height: 16),
            const Text(
              '📋 行動建議',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            ...actionItems!.map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('✓ ', style: TextStyle(fontSize: 18, color: Colors.green)),
                  Expanded(child: Text(item, style: const TextStyle(fontSize: 16))),
                ],
              ),
            )),
          ],
        ],
      ),
    );
  }
}
