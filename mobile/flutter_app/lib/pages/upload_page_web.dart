/// Web-specific stub for UploadPage (no File support)
import 'package:flutter/material.dart';

Widget buildFileImagePreview(String path) {
  // This should never be called on Web
  return const Icon(Icons.error, size: 120);
}
