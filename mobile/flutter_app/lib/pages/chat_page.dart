import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../services/chat_service.dart';
import '../state/app_state.dart';

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  bool _sending = false;

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final history = ref.watch(chatHistoryProvider);
    final userProfile = ref.watch(userProfileProvider);
    final report = ref.watch(reportProvider);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('AI 對話', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              TextButton(
                onPressed: history.isEmpty ? null : _confirmClear,
                child: const Text('清除對話'),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            controller: _scrollController,
            padding: const EdgeInsets.all(12),
            itemCount: history.length + (_sending ? 1 : 0),
            itemBuilder: (context, index) {
              if (index >= history.length) {
                return _buildTypingIndicator();
              }
              final msg = history[index];
              return _buildMessageBubble(msg);
            },
          ),
        ),
        if (userProfile == null)
          const Padding(
            padding: EdgeInsets.all(12),
            child: Text('⚠️ 請先在個人資料頁完成檔案建立。', style: TextStyle(color: Colors.red)),
          ),
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: const InputDecoration(
                    hintText: '輸入問題...',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                onPressed: _sending ? null : () => _sendMessage(userProfile, report),
                icon: _sending ? const CircularProgressIndicator() : const Icon(Icons.send),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMessageBubble(Map<String, dynamic> msg) {
    final isUser = msg['role'] == 'user';
    final content = msg['content'] ?? '';
    final ts = _formatTime(msg['timestamp'] as String?);

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isUser ? Colors.green.shade100 : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 用戶訊息使用普通 Text，AI 訊息使用 Markdown 渲染
            if (isUser)
              Text(content, style: const TextStyle(fontSize: 15))
            else
              MarkdownBody(
                data: content,
                styleSheet: MarkdownStyleSheet(
                  p: const TextStyle(fontSize: 15, height: 1.5),
                  strong: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.green.shade800,
                  ),
                  listBullet: const TextStyle(fontSize: 15),
                  blockSpacing: 8.0,
                  h1: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                  h2: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                  h3: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                  code: TextStyle(
                    backgroundColor: Colors.grey.shade300,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
            if (ts.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(ts, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
            ]
          ],
        ),
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.grey.shade200,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('AI 輸入中'),
            const SizedBox(width: 8),
            SizedBox(
              width: 24,
              height: 16,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildTypingDot(0),
                  _buildTypingDot(1),
                  _buildTypingDot(2),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTypingDot(int index) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 600),
      builder: (context, value, child) {
        final delay = index * 0.2;
        final animValue = (value + delay) % 1.0;
        final opacity = (animValue < 0.5) ? animValue * 2 : (1 - animValue) * 2;
        
        return Container(
          width: 6,
          height: 6,
          decoration: BoxDecoration(
            color: Colors.grey.shade600.withOpacity(opacity.clamp(0.2, 1.0)),
            shape: BoxShape.circle,
          ),
        );
      },
      onEnd: () {
        // 重複動畫
        if (mounted && _sending) {
          setState(() {});
        }
      },
    );
  }

  String _formatTime(String? iso) {
    if (iso == null) return '';
    final dt = DateTime.tryParse(iso);
    if (dt == null) return '';
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _confirmClear() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('清除對話'),
        content: const Text('確定要清除目前的聊天記錄嗎？'),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('取消')),
          ElevatedButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('清除')),
        ],
      ),
    );

    if (confirmed == true) {
      ref.read(chatHistoryProvider.notifier).state = [];
    }
  }

  Future<void> _sendMessage(Map<String, dynamic>? userProfile, Map<String, dynamic>? report) async {
    if (userProfile == null) {
      return;
    }
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    _controller.clear();
    setState(() => _sending = true);

    final history = ref.read(chatHistoryProvider.notifier).state;
    final newHistory = List<Map<String, dynamic>>.from(history)
      ..add({'role': 'user', 'content': text, 'timestamp': DateTime.now().toIso8601String()});
    ref.read(chatHistoryProvider.notifier).state = newHistory;
    _scrollToBottom();

    try {
      final payload = {
        'user_id': userProfile['id'],
        'message': text,
        'context': report,
        'history': newHistory.map((e) => {'role': e['role'], 'content': e['content']}).toList(),
      };

      final response = await ChatService().sendMessage(payload);
      final reply = response['reply'] ?? '抱歉，請稍後再試。';

      ref.read(chatHistoryProvider.notifier).state = [
        ...newHistory,
        {'role': 'assistant', 'content': reply, 'timestamp': DateTime.now().toIso8601String()},
      ];
      _scrollToBottom();
    } catch (e) {
      ref.read(chatHistoryProvider.notifier).state = [
        ...newHistory,
        {'role': 'assistant', 'content': '發生錯誤：$e', 'timestamp': DateTime.now().toIso8601String()},
      ];
      _scrollToBottom();
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }
}
