import 'package:flutter/material.dart';

/// Stub for UploadPage on Web
/// The actual UploadPage uses dart:io which is not available on Web
class UploadPage extends StatelessWidget {
  const UploadPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.no_photography_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              '檔案上傳功能暫不支援 Web 版',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              '請使用手機 App 進行照片拍攝與檔案上傳',
              style: TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
