/// Cross-platform file handling
/// Uses dart:io on native platforms and stub on Web
export 'file_stub.dart'
    if (dart.library.io) 'file_io.dart';
