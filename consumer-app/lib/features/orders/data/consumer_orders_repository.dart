import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../domain/consumer_order_model.dart';

final consumerOrdersRepositoryProvider = Provider<ConsumerOrdersRepository>((ref) {
  return ConsumerOrdersRepository(apiClient: ApiClient());
});

/// Repository interfacing with backend Consumer Order endpoints (`/api/v1/orders/my`).
class ConsumerOrdersRepository {
  final ApiClient _apiClient;

  ConsumerOrdersRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Fetches order history for current consumer user.
  Future<List<ConsumerOrderModel>> getMyOrders() async {
    final response = await _apiClient.get('/orders/my');
    if (response.statusCode == 200 && response.data != null) {
      final body = response.data as Map<String, dynamic>;
      final rawList = body['data'] as List<dynamic>? ?? [];
      return rawList
          .map((item) => ConsumerOrderModel.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// Fetches detailed consumer order view by ID.
  Future<ConsumerOrderModel?> getMyOrderById(String orderId) async {
    final response = await _apiClient.get('/orders/my/$orderId');
    if (response.statusCode == 200 && response.data != null) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>?;
      if (rawData != null) {
        return ConsumerOrderModel.fromJson(rawData);
      }
    }
    return null;
  }

  /// Cancels a consumer order pre-shipment.
  Future<ConsumerOrderModel> cancelOrder(String orderId) async {
    final response = await _apiClient.post('/orders/$orderId/cancel');
    if (response.statusCode == 200 && response.data != null) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>;
      return ConsumerOrderModel.fromJson(rawData);
    }
    throw Exception('Failed to cancel order');
  }
}
