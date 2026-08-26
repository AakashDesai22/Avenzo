import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../domain/cart_model.dart';

final cartRepositoryProvider = Provider<CartRepository>((ref) {
  return CartRepository(apiClient: ApiClient());
});

/// Repository interfacing with backend Consumer Cart endpoints (`/api/v1/cart`).
class CartRepository {
  final ApiClient _apiClient;

  CartRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Fetches active consumer shopping cart.
  Future<CartModel> getCart() async {
    final response = await _apiClient.get('/cart');
    if (response.statusCode == 200 && response.data != null) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>;
      return CartModel.fromJson(rawData);
    }
    throw Exception('Failed to load consumer cart');
  }

  /// Adds a product item to active cart.
  Future<CartModel> addItem({required String productId, int quantity = 1}) async {
    final response = await _apiClient.post(
      '/cart/items',
      data: {
        'product_id': productId,
        'quantity': quantity,
      },
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>;
      return CartModel.fromJson(rawData);
    }
    throw Exception('Failed to add item to cart');
  }

  /// Updates quantity of an existing cart item.
  Future<CartModel> updateItem({required String itemId, required int quantity}) async {
    final response = await _apiClient.put(
      '/cart/items/$itemId',
      data: {
        'quantity': quantity,
      },
    );

    if (response.statusCode == 200) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>;
      return CartModel.fromJson(rawData);
    }
    throw Exception('Failed to update cart item quantity');
  }

  /// Removes an item from cart.
  Future<CartModel> removeItem(String itemId) async {
    final response = await _apiClient.delete('/cart/items/$itemId');
    if (response.statusCode == 200) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>;
      return CartModel.fromJson(rawData);
    }
    throw Exception('Failed to remove item from cart');
  }

  /// Clears all items from cart.
  Future<CartModel> clearCart() async {
    final response = await _apiClient.delete('/cart');
    if (response.statusCode == 200) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>;
      return CartModel.fromJson(rawData);
    }
    throw Exception('Failed to clear cart');
  }
}
