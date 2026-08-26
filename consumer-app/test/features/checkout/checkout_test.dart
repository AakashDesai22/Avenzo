import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/core/utils/uuid_generator.dart';
import 'package:avenzo_consumer/features/checkout/data/checkout_repository.dart';
import 'package:avenzo_consumer/features/checkout/providers/checkout_provider.dart';
import 'package:avenzo_consumer/core/network/api_client.dart';
import 'package:dio/dio.dart';

class MockApiClientForCheckout extends ApiClient {
  Map<String, dynamic> mockOrderData = {};

  MockApiClientForCheckout() : super(customDio: Dio());

  @override
  Future<Response<T>> post<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': mockOrderData} as T,
    );
  }
}

void main() {
  final orderJson = {
    'id': 'ord-505',
    'order_number': 'ORD-2026-0099',
    'user_id': 'user-11',
    'status': 'PENDING',
    'payment_status': 'UNPAID',
    'payment_method': 'MOCK_PAYMENT',
    'subtotal': 130.00,
    'delivery_fee': 25.00,
    'total_amount': 155.00,
    'shipping_address': '123 Main St, Austin TX',
    'items': [],
  };

  group('UuidGenerator Suite', () {
    test('UuidGenerator produces valid RFC 4122 v4 format', () {
      final uuid1 = UuidGenerator.generateV4();
      final uuid2 = UuidGenerator.generateV4();

      expect(uuid1, isNot(equals(uuid2)));
      expect(RegExp(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$').hasMatch(uuid1), true);
    });
  });

  group('CheckoutNotifier & Idempotency Key Suite', () {
    test('CheckoutNotifier initializes with valid Idempotency-Key', () {
      final mockClient = MockApiClientForCheckout()..mockOrderData = orderJson;
      final repo = CheckoutRepository(apiClient: mockClient);
      final notifier = CheckoutNotifier(repository: repo);

      expect(notifier.state.idempotencyKey, isNotEmpty);
      final key1 = notifier.state.idempotencyKey;

      notifier.initCheckout();
      final key2 = notifier.state.idempotencyKey;
      expect(key1, isNot(equals(key2)));
    });

    test('CheckoutNotifier submitCheckout creates order', () async {
      final mockClient = MockApiClientForCheckout()..mockOrderData = orderJson;
      final repo = CheckoutRepository(apiClient: mockClient);
      final notifier = CheckoutNotifier(repository: repo);

      final order = await notifier.submitCheckout(
        shippingAddress: '123 Main St, Austin TX',
        paymentMethod: 'MOCK_PAYMENT',
      );

      expect(order, isNotNull);
      expect(order?.id, 'ord-505');
      expect(order?.orderNumber, 'ORD-2026-0099');
      expect(order?.totalAmount, 155.00);
    });
  });
}
