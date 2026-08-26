import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/features/orders/domain/consumer_order_model.dart';
import 'package:avenzo_consumer/features/orders/data/consumer_orders_repository.dart';
import 'package:avenzo_consumer/features/orders/providers/consumer_orders_provider.dart';
import 'package:avenzo_consumer/core/network/api_client.dart';
import 'package:dio/dio.dart';

class MockApiClientForOrders extends ApiClient {
  List<Map<String, dynamic>> mockOrdersList = [];
  Map<String, dynamic> mockOrderData = {};

  MockApiClientForOrders() : super(customDio: Dio());

  @override
  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters, Options? options}) async {
    if (path == '/orders/my') {
      return Response<T>(
        requestOptions: RequestOptions(path: path),
        statusCode: 200,
        data: {'success': true, 'data': mockOrdersList} as T,
      );
    }
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': mockOrderData} as T,
    );
  }

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
    'items': [
      {
        'id': 'item-1',
        'order_id': 'ord-505',
        'product_id': 'prod-101',
        'quantity': 2,
        'unit_price': 65.00,
        'total_price': 130.00,
        'fulfillment_status': 'UNALLOCATED',
      },
    ],
  };

  group('ConsumerOrderModel Suite', () {
    test('ConsumerOrderModel parses JSON and checks cancellation eligibility', () {
      final order = ConsumerOrderModel.fromJson(orderJson);
      expect(order.id, 'ord-505');
      expect(order.orderNumber, 'ORD-2026-0099');
      expect(order.canCancel, true);

      final shippedOrderJson = Map<String, dynamic>.from(orderJson)..['status'] = 'SHIPPED';
      final shippedOrder = ConsumerOrderModel.fromJson(shippedOrderJson);
      expect(shippedOrder.canCancel, false);
    });
  });

  group('ConsumerOrdersNotifier Suite', () {
    test('ConsumerOrdersNotifier loads my orders', () async {
      final mockClient = MockApiClientForOrders()..mockOrdersList = [orderJson];
      final repo = ConsumerOrdersRepository(apiClient: mockClient);
      final notifier = ConsumerOrdersNotifier(repository: repo);

      await Future.delayed(const Duration(milliseconds: 50));
      expect(notifier.state.orders.length, 1);
      expect(notifier.state.orders.first.id, 'ord-505');
    });

    test('ConsumerOrdersNotifier cancels order', () async {
      final cancelledJson = Map<String, dynamic>.from(orderJson)..['status'] = 'CANCELLED';
      final mockClient = MockApiClientForOrders()
        ..mockOrdersList = [orderJson]
        ..mockOrderData = cancelledJson;
      final repo = ConsumerOrdersRepository(apiClient: mockClient);
      final notifier = ConsumerOrdersNotifier(repository: repo);

      await Future.delayed(const Duration(milliseconds: 50));
      final success = await notifier.cancelOrder('ord-505');
      expect(success, true);
      expect(notifier.state.selectedOrder?.status, 'CANCELLED');
    });
  });
}
