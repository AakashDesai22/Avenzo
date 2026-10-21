import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/features/marketplace/domain/category_model.dart';
import 'package:avenzo_consumer/features/marketplace/domain/marketplace_product_model.dart';
import 'package:avenzo_consumer/features/marketplace/data/marketplace_repository.dart';
import 'package:avenzo_consumer/features/marketplace/providers/marketplace_provider.dart';
import 'package:avenzo_consumer/features/marketplace/presentation/marketplace_screen.dart';
import 'package:avenzo_consumer/core/network/api_client.dart';
import 'package:avenzo_consumer/features/cart/data/cart_repository.dart';
import 'package:avenzo_consumer/features/cart/domain/cart_model.dart';
import 'package:dio/dio.dart';

class MockApiClientForMarketplace extends ApiClient {
  bool getSuccess = true;
  List<Map<String, dynamic>> mockProducts = [];
  List<Map<String, dynamic>> mockCategories = [];
  Map<String, dynamic>? mockProductDetail;
  String? lastPath;
  Map<String, dynamic>? lastQueryParams;

  MockApiClientForMarketplace() : super(customDio: Dio());

  @override
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    lastPath = path;
    lastQueryParams = queryParameters;

    if (!getSuccess) {
      throw Exception('Network connection error');
    }

    if (path == '/categories') {
      return Response<T>(
        requestOptions: RequestOptions(path: path),
        statusCode: 200,
        data: {
          'success': true,
          'data': mockCategories,
        } as T,
      );
    }

    if (path.startsWith('/marketplace/products/')) {
      return Response<T>(
        requestOptions: RequestOptions(path: path),
        statusCode: 200,
        data: {
          'success': true,
          'data': mockProductDetail,
        } as T,
      );
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

class MockCartRepositoryForMarketplace extends CartRepository {
  MockCartRepositoryForMarketplace() : super(apiClient: MockApiClientForMarketplace());

  @override
  Future<CartModel> getCart() async {
    return const CartModel(id: 'cart-1', userId: 'usr-1', status: 'ACTIVE');
  }
}

void main() {
  final testProductJson = {
    'id': 'prod-101',
    'name': 'Fresh Organic Milk 1L',
    'description': 'Pasteurized whole milk from local dairy',
    'sku': 'MILK-101',
    'barcode': '8901234567890',
    'category_id': 'cat-dairy-1',
    'category': {'id': 'cat-dairy-1', 'name': 'Dairy & Eggs'},
    'brand_id': 'brand-farm',
    'brand': {'id': 'brand-farm', 'name': 'Farm Fresh'},
    'unit_of_measure': 'Liters',
    'unit_price': 65.50,
    'shelf_life_days': 7,
    'has_expiry': true,
    'image_url': 'https://example.com/milk.png',
    'is_active': true,
    'available_quantity': 25,
    'is_available': true,
  };

  final testOutOfStockProductJson = {
    'id': 'prod-102',
    'name': 'Artisan Sourdough Bread',
    'description': 'Freshly baked sourdough loaf',
    'sku': 'BREAD-202',
    'barcode': '8901234567891',
    'category_id': 'cat-bakery-2',
    'category': {'id': 'cat-bakery-2', 'name': 'Bakery'},
    'brand_id': null,
    'brand': null,
    'unit_of_measure': 'loaves',
    'unit_price': 45.00,
    'shelf_life_days': 3,
    'has_expiry': true,
    'image_url': null,
    'is_active': true,
    'available_quantity': 0,
    'is_available': false,
  };

  final testCategoryJson = {
    'id': 'cat-dairy-1',
    'name': 'Dairy & Eggs',
    'parent_id': null,
    'description': 'Fresh milk, yogurt, and farm eggs',
    'is_active': true,
    'created_at': '2026-10-20T12:00:00Z',
    'updated_at': '2026-10-20T12:00:00Z',
  };

  group('CategoryModel Suite', () {
    test('CategoryModel parses JSON correctly', () {
      final model = CategoryModel.fromJson(testCategoryJson);
      expect(model.id, 'cat-dairy-1');
      expect(model.name, 'Dairy & Eggs');
      expect(model.description, 'Fresh milk, yogurt, and farm eggs');
      expect(model.isActive, true);
      expect(model.createdAt, isNotNull);
    });

    test('CategoryModel converts to JSON and props compare correctly', () {
      final model1 = CategoryModel.fromJson(testCategoryJson);
      final model2 = CategoryModel.fromJson(testCategoryJson);
      expect(model1, equals(model2));
      final json = model1.toJson();
      expect(json['id'], 'cat-dairy-1');
      expect(json['name'], 'Dairy & Eggs');
    });
  });

  group('MarketplaceProductModel Suite', () {
    test('MarketplaceProductModel parses JSON with all live fields correctly', () {
      final model = MarketplaceProductModel.fromJson(testProductJson);
      expect(model.id, 'prod-101');
      expect(model.name, 'Fresh Organic Milk 1L');
      expect(model.description, 'Pasteurized whole milk from local dairy');
      expect(model.sku, 'MILK-101');
      expect(model.barcode, '8901234567890');
      expect(model.categoryId, 'cat-dairy-1');
      expect(model.categoryName, 'Dairy & Eggs');
      expect(model.brandName, 'Farm Fresh');
      expect(model.unitPrice, 65.50);
      expect(model.shelfLifeDays, 7);
      expect(model.hasExpiry, true);
      expect(model.imageUrl, 'https://example.com/milk.png');
      expect(model.availableQuantity, 25);
      expect(model.isAvailable, true);
    });

    test('MarketplaceProductModel handles out of stock product correctly', () {
      final model = MarketplaceProductModel.fromJson(testOutOfStockProductJson);
      expect(model.id, 'prod-102');
      expect(model.isAvailable, false);
      expect(model.availableQuantity, 0);
      expect(model.imageUrl, isNull);
    });

    test('MarketplaceProductModel parses price as string or number gracefully', () {
      final stringPriceJson = Map<String, dynamic>.from(testProductJson);
      stringPriceJson['unit_price'] = '99.75';
      final model = MarketplaceProductModel.fromJson(stringPriceJson);
      expect(model.unitPrice, 99.75);
    });
  });

  group('MarketplaceRepository Suite', () {
    test('getCategories fetches and parses category list', () async {
      final mockClient = MockApiClientForMarketplace()..mockCategories = [testCategoryJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final categories = await repo.getCategories();

      expect(categories.length, 1);
      expect(categories.first.id, 'cat-dairy-1');
      expect(categories.first.name, 'Dairy & Eggs');
      expect(mockClient.lastPath, '/categories');
    });

    test('getProducts parses returned catalog list with filters', () async {
      final mockClient = MockApiClientForMarketplace()..mockProducts = [testProductJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final products = await repo.getProducts(
        categoryId: 'cat-dairy-1',
        search: 'milk',
        inStockOnly: true,
      );

      expect(products.length, 1);
      expect(products.first.name, 'Fresh Organic Milk 1L');
      expect(mockClient.lastPath, '/marketplace/products');
      expect(mockClient.lastQueryParams?['category_id'], 'cat-dairy-1');
      expect(mockClient.lastQueryParams?['search'], 'milk');
      expect(mockClient.lastQueryParams?['in_stock_only'], true);
    });

    test('getProductById fetches product details', () async {
      final mockClient = MockApiClientForMarketplace()..mockProductDetail = testProductJson;
      final repo = MarketplaceRepository(apiClient: mockClient);
      final product = await repo.getProductById('prod-101');

      expect(product, isNotNull);
      expect(product!.id, 'prod-101');
      expect(mockClient.lastPath, '/marketplace/products/prod-101');
    });
  });

  group('MarketplaceNotifier Suite', () {
    test('MarketplaceNotifier loads both categories and products on init', () async {
      final mockClient = MockApiClientForMarketplace()
        ..mockCategories = [testCategoryJson]
        ..mockProducts = [testProductJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final notifier = MarketplaceNotifier(repository: repo);

      await Future.delayed(const Duration(milliseconds: 50));
      expect(notifier.state.isLoading, false);
      expect(notifier.state.categories.length, 1);
      expect(notifier.state.categories.first.name, 'Dairy & Eggs');
      expect(notifier.state.products.length, 1);
      expect(notifier.state.products.first.name, 'Fresh Organic Milk 1L');
    });

    test('selectCategory toggles category filter and reloads', () async {
      final mockClient = MockApiClientForMarketplace()
        ..mockCategories = [testCategoryJson]
        ..mockProducts = [testProductJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final notifier = MarketplaceNotifier(repository: repo);

      notifier.selectCategory('cat-dairy-1');
      expect(notifier.state.selectedCategoryId, 'cat-dairy-1');

      // Toggling the same category deselects it
      notifier.selectCategory('cat-dairy-1');
      expect(notifier.state.selectedCategoryId, isNull);
    });

    test('toggleInStockOnly switches stock filter and reloads', () async {
      final mockClient = MockApiClientForMarketplace()
        ..mockProducts = [testProductJson];
      final repo = MarketplaceRepository(apiClient: mockClient);
      final notifier = MarketplaceNotifier(repository: repo);

      expect(notifier.state.inStockOnly, false);
      notifier.toggleInStockOnly();
      expect(notifier.state.inStockOnly, true);
    });

    test('Handles live published vs unpublished product workflow after refresh', () async {
      final mockClient = MockApiClientForMarketplace()
        ..mockProducts = [testProductJson]; // Initially has 1 published product
      final repo = MarketplaceRepository(apiClient: mockClient);
      final notifier = MarketplaceNotifier(repository: repo);

      await Future.delayed(const Duration(milliseconds: 50));
      expect(notifier.state.products.length, 1);

      // Business unpublishes product -> server returns empty list
      mockClient.mockProducts = [];
      await notifier.refresh();
      expect(notifier.state.products, isEmpty);

      // Business publishes 2 products -> server returns both
      mockClient.mockProducts = [testProductJson, testOutOfStockProductJson];
      await notifier.refresh();
      expect(notifier.state.products.length, 2);
    });

    test('Sets error message when API call fails and clears on retry', () async {
      final mockClient = MockApiClientForMarketplace()..getSuccess = false;
      final repo = MarketplaceRepository(apiClient: mockClient);
      final notifier = MarketplaceNotifier(repository: repo);

      await Future.delayed(const Duration(milliseconds: 50));
      expect(notifier.state.isLoading, false);
      expect(notifier.state.errorMessage, isNotNull);

      // Retry after connection restores
      mockClient.getSuccess = true;
      mockClient.mockProducts = [testProductJson];
      await notifier.loadProducts();
      expect(notifier.state.errorMessage, isNull);
      expect(notifier.state.products.length, 1);
    });
  });

  group('MarketplaceScreen Widget Suite', () {
    testWidgets('Renders categories chips, in-stock filter, and product cards', (tester) async {
      final mockClient = MockApiClientForMarketplace()
        ..mockCategories = [testCategoryJson]
        ..mockProducts = [testProductJson];
      final repo = MarketplaceRepository(apiClient: mockClient);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            marketplaceRepositoryProvider.overrideWithValue(repo),
            cartRepositoryProvider.overrideWithValue(MockCartRepositoryForMarketplace()),
          ],
          child: const MaterialApp(
            home: MarketplaceScreen(),
          ),
        ),
      );

      // Let initial async data load
      await tester.pumpAndSettle();

      // Category chips rendered
      expect(find.text('All'), findsOneWidget);
      expect(find.text('Dairy & Eggs'), findsOneWidget);

      // Filter chip rendered
      expect(find.text('In Stock Only'), findsOneWidget);

      // Product card rendered
      expect(find.text('Fresh Organic Milk 1L'), findsOneWidget);
      expect(find.text('In Stock'), findsOneWidget);
    });

    testWidgets('Renders empty state when no products match', (tester) async {
      final mockClient = MockApiClientForMarketplace()
        ..mockCategories = [testCategoryJson]
        ..mockProducts = [];
      final repo = MarketplaceRepository(apiClient: mockClient);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            marketplaceRepositoryProvider.overrideWithValue(repo),
            cartRepositoryProvider.overrideWithValue(MockCartRepositoryForMarketplace()),
          ],
          child: const MaterialApp(
            home: MarketplaceScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('No products found matching your search.'), findsOneWidget);
    });

    testWidgets('Renders error state with Retry button on API failure', (tester) async {
      final mockClient = MockApiClientForMarketplace()..getSuccess = false;
      final repo = MarketplaceRepository(apiClient: mockClient);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            marketplaceRepositoryProvider.overrideWithValue(repo),
            cartRepositoryProvider.overrideWithValue(MockCartRepositoryForMarketplace()),
          ],
          child: const MaterialApp(
            home: MarketplaceScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Retry'), findsOneWidget);
      expect(find.text('Failed to load products. Please check your connection.'), findsOneWidget);
    });
  });
}
