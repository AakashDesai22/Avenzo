import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../orders/domain/consumer_order_model.dart';

final checkoutRepositoryProvider = Provider<CheckoutRepository>((ref) {
  return CheckoutRepository(apiClient: ApiClient());
});

/// Repository interfacing with backend Consumer Checkout endpoints (`POST /api/v1/orders`).
class CheckoutRepository {
  final ApiClient _apiClient;

  CheckoutRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Processes checkout for active cart with optional Idempotency-Key header.
  Future<ConsumerOrderModel> checkout({
    required String shippingAddress,
    String? notes,
    String paymentMethod = 'MOCK_PAYMENT',
    required String idempotencyKey,
  }) async {
    final response = await _apiClient.post(
      '/orders',
      data: {
        'shipping_address': shippingAddress,
        'notes': notes,
        'payment_method': paymentMethod,
      },
      options: Options(
        headers: {
          'Idempotency-Key': idempotencyKey,
        },
      ),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>;
      return ConsumerOrderModel.fromJson(rawData);
    }

    throw Exception('Checkout failed. Please try again.');
  }
}
