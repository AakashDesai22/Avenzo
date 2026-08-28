import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/models/consumer_analytics_model.dart';

/// Repository managing Consumer Waste Analytics API interactions.
class AnalyticsRepository {
  final ApiClient _apiClient;

  AnalyticsRepository({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  /// Retrieves personal consumer waste reduction analytics and score.
  Future<ConsumerWasteMetricsModel> getConsumerWasteAnalytics() async {
    try {
      final response = await _apiClient.get('/analytics/consumer');
      final data = response.data;
      if (data is Map<String, dynamic>) {
        if (data.containsKey('data') && data['data'] != null) {
          return ConsumerWasteMetricsModel.fromJson(data['data'] as Map<String, dynamic>);
        }
        return ConsumerWasteMetricsModel.fromJson(data);
      }
      throw ApiException(message: 'Invalid analytics response structure.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to fetch waste analytics: $e');
    }
  }
}
