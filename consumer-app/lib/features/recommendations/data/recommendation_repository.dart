import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import 'recommendation_models.dart';

/// Repository managing Consumer Recommendations API interactions.
class RecommendationRepository {
  final ApiClient _apiClient;

  RecommendationRepository({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  /// Retrieves active recommendations for the authenticated consumer.
  Future<List<RecommendationModel>> getRecommendations() async {
    try {
      final response = await _apiClient.get('/recommendations');
      final data = response.data;
      if (data is List) {
        return data
            .map((e) => RecommendationModel.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return [];
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to fetch recommendations: $e');
    }
  }

  /// Retrieves aggregate consumer intelligence summary metrics.
  Future<RecommendationSummaryModel> getSummary() async {
    try {
      final response = await _apiClient.get('/recommendations/summary');
      return RecommendationSummaryModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to fetch intelligence summary: $e');
    }
  }

  /// Dismisses a recommendation by ID.
  Future<RecommendationModel> dismissRecommendation(String recommendationId) async {
    try {
      final response = await _apiClient.post(
        '/recommendations/$recommendationId/dismiss',
      );
      return RecommendationModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to dismiss recommendation: $e');
    }
  }

  /// Refreshes recommendations from backend intelligence engine.
  Future<List<RecommendationModel>> refreshRecommendations() async {
    try {
      final response = await _apiClient.post('/recommendations/refresh');
      final data = response.data;
      if (data is List) {
        return data
            .map((e) => RecommendationModel.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return [];
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to refresh recommendations: $e');
    }
  }
}
