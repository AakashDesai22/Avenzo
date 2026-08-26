import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/features/marketplace/domain/marketplace_product_model.dart';
import 'package:avenzo_consumer/features/marketplace/data/marketplace_repository.dart';
import 'package:avenzo_consumer/features/marketplace/providers/marketplace_provider.dart';
import 'package:avenzo_consumer/core/network/api_client.dart';
import 'package:dio/dio.dart';

class MockApiClientForMarketplace extends ApiClient {
  bool getSuccess = true;
  List<Map<String, dynamic>> mockProducts = [];

  MockApiClientForMarketplace() : super(customDio: Dio());

  @override
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    if (!getSuccess) {
      throw Exception('Network error');
    }
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {
        'success': true,
        'data': mockProducts,
      } as T,
    );
  }
}

void main() {
  final testJson = {
    'id': 'prod-101',
    'name': 'Fresh Organic Milk 1L',
    'description': 'Pasteurized whole milk',
    'sku': 'MILK-101',
    'barcode': '8901234567890',
    'category_id': 'cat-dairy',
    'category': {'name': 'Dairy'},
    'brand_id': 'brand-farm',
    'brand': {'name': 'Farm Fresh'},
    'unit_of_measure': 'Liters',
    'unit_price': 65.50,
    'shelf_life_days': 7,
    'has_expiry': true,
    'image_url': 'https://example.com/milk.png',
    'is_active': true,
    'available_quantity': 25,
    'is_available': true,
  };

  group('MarketplaceProductModel Suite', () {
    test('MarketplaceProductModel parses JSON correctly', () {
      final model = MarketplaceProductModel.fromJson(testJson);
      expect(model.id, 'prod-101');
      expect(model.name, 'Fresh Organic Milk 1L');
      expect(model.unitPrice, 65.50);
      expect(model.availableQuantity, 25);
      expect(model.isAvailable, true);
      expect(model.categoryName, 'Dairy');
    });
  });

  group('MarketplaceRepository Suite', () {
    test('getProducts parses returned catalog list', () async {
      final mockClient = MockApiClientForMarketplace()..mockProducts = [testJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final list = await repo.getProducts();

      expect(list.length, 1);
      expect(list.first.name, 'Fresh Organic Milk 1L');
    });
  });

  group('MarketplaceNotifier Suite', () {
    test('MarketplaceNotifier loads products and updates state', () async {
      final mockClient = MockApiClientForMarketplace()..mockProducts = [testJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final notifier = MarketplaceNotifier(repository: repo);

      await Future.delayed(const Duration(milliseconds: 50));
      expect(notifier.state.isLoading, false);
      expect(notifier.state.products.length, 1);
    });

    test('selectCategory updates category filter and reloads', () async {
      final mockClient = MockApiClientForMarketplace()..mockProducts = [testJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final notifier = MarketplaceNotifier(repository: repo);

      notifier.selectCategory('cat-dairy');
      expect(notifier.state.selectedCategoryId, 'cat-dairy');
    });
  });
}
