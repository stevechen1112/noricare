/// IO-specific image preview for UploadPage (non-Web platforms)
import 'dart:io';
import 'package:flutter/material.dart';

Widget buildFileImagePreview(String path) {
  return Image.file(
    File(path),
    height: 120,
    width: 120,
    fit: BoxFit.cover,
  );
}
