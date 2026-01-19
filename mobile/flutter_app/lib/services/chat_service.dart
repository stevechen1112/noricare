import 'api_client.dart';

class ChatService {
  Future<Map<String, dynamic>> sendMessage(Map<String, dynamic> payload) async {
    final response = await ApiClient.instance.dio.post('/chat/message', data: payload);
    return response.data as Map<String, dynamic>;
  }
}
