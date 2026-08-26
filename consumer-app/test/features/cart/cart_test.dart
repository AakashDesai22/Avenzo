import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/features/cart/domain/cart_model.dart';
import 'package:avenzo_consumer/features/cart/data/cart_repository.dart';
import 'package:avenzo_consumer/features/cart/providers/cart_provider.dart';
import 'package:avenzo_consumer/core/network/api_client.dart';
import 'package:dio/dio.dart';

class MockApiClientForCart extends ApiClient {
  Map<String, dynamic> mockCartData = {};

  MockApiClientForCart() : super(customDio: Dio());

  @override
  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters, Options? options}) async {
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': mockCartData} as T,
    );
  }

  @override
  Future<Response<T>> post<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': mockCartData} as T,
    );
  }

  @override
  Future<Response<T>> put<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': mockCartData} as T,
    );
  }

  @override
  Future<Response<T>> delete<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': mockCartData} as T,
    );
  }
}

void main() {
  final cartJson = {
    'id': 'cart-202',
    'user_id': 'user-11',
    'status': 'ACTIVE',
    'total_items_count': 1,
    'calculated_subtotal': 130.00,
    'items': [
      {
        'id': 'item-1',
        'cart_id': 'cart-202',
        'product_id': 'prod-101',
        'quantity': 2,
        'product': {
          'id': 'prod-101',
          'name': 'Fresh Organic Milk 1L',
          'sku': 'MILK-101',
          'category_id': 'cat-dairy',
          'unit_of_measure': 'Liters',
          'unit_price': 65.00,
          'has_expiry': true,
          'is_active': true,
          'available_quantity': 10,
          'is_available': true,
        },
      },
    ],
  };

  group('CartModel & CartItemModel Suite', () {
    test('CartModel parses JSON and calculates line total', () {
      final cart = CartModel.fromJson(cartJson);
      expect(cart.id, 'cart-202');
      expect(cart.items.length, 1);
      expect(cart.items.first.itemTotal, 130.00);
      expect(cart.calculatedSubtotal, 130.00);
      expect(cart.hasUnavailableItems, false);
    });

    test('CartModel flags unavailable items correctly', () {
      final unavailableJson = Map<String, dynamic>.from(cartJson);
      unavailableJson['items'] = [
        {
          'id': 'item-1',
          'cart_id': 'cart-202',
          'product_id': 'prod-101',
          'quantity': 15, // exceeds available stock 10
          'product': {
            'id': 'prod-101',
            'name': 'Fresh Organic Milk 1L',
            'sku': 'MILK-101',
            'category_id': 'cat-dairy',
            'unit_of_measure': 'Liters',
            'unit_price': 65.00,
            'has_expiry': true,
            'is_active': true,
            'available_quantity': 10,
            'is_available': true,
          },
        },
      ];

      final cart = CartModel.fromJson(unavailableJson);
      expect(cart.hasUnavailableItems, true);
    });
  });

  group('CartNotifier Suite', () {
    test('CartNotifier loads active cart', () async {
      final mockClient = MockApiClientForCart()..mockCartData = cartJson;
      final repo = CartRepository(apiClient: mockClient);
      final notifier = CartNotifier(repository: repo);

      await Future.delayed(const Duration(milliseconds: 50));
      expect(notifier.state.cart?.id, 'cart-202');
      expect(notifier.state.subtotal, 130.00);
    });

    test('CartNotifier addToCart calls repository', () async {
      final mockClient = MockApiClientForCart()..mockCartData = cartJson;
      final repo = CartRepository(apiClient: mockClient);
      final notifier = CartNotifier(repository: repo);

      final success = await notifier.addToCart('prod-101', quantity: 2);
      expect(success, true);
      expect(notifier.state.cart?.totalItemsCount, 1);
    });
  });
}
