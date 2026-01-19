import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';
import '../models/meal.dart';
import '../models/food_vision.dart';
import 'api_client.dart';

class MealService {
  final Dio _dio = ApiClient.instance.dio;

  Future<FoodAlignResponse> alignFood(String query, {int limit = 5}) async {
    final response = await _dio.get(
      '/food/align',
      queryParameters: {'q': query, 'limit': limit},
    );
    return FoodAlignResponse.fromJson(response.data);
  }

  Future<MealResponse> createMeal({
    required List<MealItemDraft> items,
    String source = 'manual',
    String? note,
  }) async {
    final response = await _dio.post(
      '/meals',
      data: {
        'source': source,
        'note': note,
        'items': items
            .map((e) => {
                  'food_id': e.foodId,
                  'grams': e.grams,
                  'portion_label': 'manual',
                  'raw_text': e.foodName,
                })
            .toList(),
      },
    );
    return MealResponse.fromJson(response.data);
  }

  Future<List<MealResponse>> listMeals({int limit = 10}) async {
    final response = await _dio.get(
      '/meals',
      queryParameters: {'limit': limit},
    );
    return (response.data as List<dynamic>?)
            ?.map((e) => MealResponse.fromJson(e))
            .toList() ??
        [];
  }

  Future<void> deleteMeal(String mealId) async {
    await _dio.delete('/meals/$mealId');
  }

  Future<MealSummaryResponse> mealSummary({int days = 7}) async {
    final response = await _dio.get(
      '/meals/summary',
      queryParameters: {'days': days},
    );
    return MealSummaryResponse.fromJson(response.data);
  }

  Future<FoodVisionSuggestResponse> suggestFoodFromPhoto(
    XFile imageFile, {
    int limit = 5,
    String profile = 'bento',
  }) async {
    final bytes = await imageFile.readAsBytes();
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: imageFile.name),
    });

    final response = await _dio.post(
      '/food/vision/suggest',
      queryParameters: {'limit': limit, 'profile': profile},
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
    );

    return FoodVisionSuggestResponse.fromJson(response.data);
  }
}