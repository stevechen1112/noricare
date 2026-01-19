/// Stub for cross-platform file handling
/// This file provides types that are not available on Web
class File {
  final String path;
  File(this.path);
}

class Platform {
  static String get pathSeparator => '/';
}
