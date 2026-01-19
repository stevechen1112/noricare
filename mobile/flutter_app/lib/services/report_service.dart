import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';
import 'api_client.dart';
import '../config/api_config.dart';

class ReportService {
  Future<String> uploadOcr(XFile file) async {
    final bytes = await file.readAsBytes();
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: file.name),
    });
    final response = await ApiClient.instance.dio.post('/ocr/upload', data: formData);
    return response.data['file_id'] as String;
  }

  Future<Map<String, dynamic>> getOcrResult(String fileId) async {
    final response = await ApiClient.instance.dio.get('/ocr/result/$fileId');
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> generateReport(Map<String, dynamic> payload) async {
    final response = await ApiClient.instance.dio.post(
      '/recommendation/generate',
      data: payload,
      options: Options(
        receiveTimeout: ApiConfig.aiGenerateTimeout,
      ),
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> fetchHistory(String userId) async {
    final response = await ApiClient.instance.dio.get('/users/$userId/history');
    return response.data as Map<String, dynamic>;
  }
}
