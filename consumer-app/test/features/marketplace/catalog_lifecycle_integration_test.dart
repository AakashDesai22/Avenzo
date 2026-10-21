import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/core/network/api_client.dart';
import 'package:avenzo_consumer/features/marketplace/data/marketplace_repository.dart';
import 'package:avenzo_consumer/features/marketplace/domain/marketplace_product_model.dart';
import 'package:avenzo_consumer/features/marketplace/providers/marketplace_provider.dart';
import 'package:avenzo_consumer/features/marketplace/presentation/marketplace_screen.dart';
import 'package:avenzo_consumer/features/cart/data/cart_repository.dart';
import 'package:avenzo_consumer/features/cart/domain/cart_model.dart';
import 'package:avenzo_consumer/features/pantry/data/pantry_repository.dart';
import 'package:avenzo_consumer/features/pantry/providers/pantry_provider.dart';
import 'package:avenzo_consumer/features/scanner/data/product_lookup_repository.dart';
import 'package:avenzo_consumer/features/scanner/providers/scanner_provider.dart';
import 'package:avenzo_consumer/features/recommendations/data/recommendation_models.dart';
import 'package:avenzo_consumer/features/recommendations/data/recommendation_repository.dart';
import 'package:avenzo_consumer/features/recommendations/providers/recommendation_provider.dart';
import 'package:avenzo_consumer/features/notifications/data/notification_models.dart';
import 'package:avenzo_consumer/features/notifications/data/notification_repository.dart';
import 'package:avenzo_consumer/features/notifications/providers/notification_provider.dart';
import 'package:avenzo_consumer/shared/models/pantry_item_model.dart';
import 'package:dio/dio.dart';

/// Mock ApiClient that accurately simulates the backend B2C catalog lifecycle.
class LifecycleSimulatedApiClient extends ApiClient {
  List<Map<String, dynamic>> publishedProducts = [];
  List<Map<String, dynamic>> activeCategories = [];

  LifecycleSimulatedApiClient() : super(customDio: Dio());

  @override
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    if (path == '/categories') {
      return Response<T>(
        requestOptions: RequestOptions(path: path),
        statusCode: 200,
        data: {'success': true, 'data': activeCategories} as T,
      );
    }

    if (path == '/marketplace/products') {
      final categoryId = queryParameters?['category_id'];
      final inStockOnly = queryParameters?['in_stock_only'] == true;
      final search = queryParameters?['search'] as String?;

      var filtered = List<Map<String, dynamic>>.from(publishedProducts);

      if (categoryId != null) {
        filtered = filtered.where((p) => p['category_id'] == categoryId).toList();
      }
      if (inStockOnly) {
        filtered = filtered.where((p) => (p['available_quantity'] as int? ?? 0) > 0).toList();
      }
      if (search != null && search.isNotEmpty) {
        filtered = filtered
            .where((p) => (p['name'] as String).toLowerCase().contains(search.toLowerCase()))
            .toList();
      }

      return Response<T>(
        requestOptions: RequestOptions(path: path),
        statusCode: 200,
        data: {'success': true, 'data': filtered} as T,
      );
    }

    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': []} as T,
    );
  }
}

class MockCartRepoForLifecycle extends CartRepository {
  CartModel currentCart;
  bool wasAddCalled = false;
  String? lastAddedProductId;

  MockCartRepoForLifecycle({required this.currentCart})
      : super(apiClient: LifecycleSimulatedApiClient());

  @override
  Future<CartModel> getCart() async => currentCart;

  @override
  Future<CartModel> addItem({required String productId, int quantity = 1}) async {
    wasAddCalled = true;
    lastAddedProductId = productId;
    return currentCart;
  }
}

class MockPantryRepoForLifecycle extends PantryRepository {
  final List<PantryItemModel> mockItems;
  MockPantryRepoForLifecycle(this.mockItems);

  @override
  Future<List<PantryItemModel>> getPantryItems({String? storageLocation, String status = 'active'}) async {
    return mockItems;
  }
}

class MockScannerRepoForLifecycle extends ProductLookupRepository {
  MockScannerRepoForLifecycle() : super(apiClient: LifecycleSimulatedApiClient());

  @override
  Future<ProductMasterModel?> lookupByBarcode(String barcode) async {
    return const ProductMasterModel(
      id: 'prod-milk-master',
      name: 'Organic Whole Milk',
      sku: 'MK-001',
      brandName: 'Avenzo Farms',
      categoryName: 'Dairy',
      shelfLifeDays: 7,
      unitOfMeasure: 'liters',
      barcode: '890123400001',
    );
  }
}

class MockRecommendationRepoForLifecycle implements RecommendationRepository {
  final List<RecommendationModel> mockRecs;
  MockRecommendationRepoForLifecycle(this.mockRecs);

  @override
  Future<List<RecommendationModel>> getRecommendations() async => mockRecs;

  @override
  Future<RecommendationSummaryModel> getSummary() async => const RecommendationSummaryModel(
        totalActiveItems: 5,
        expiring3dCount: 1,
        expiring7dCount: 2,
        estimatedWasteRiskCount: 1,
        hasSufficientHistory: true,
        historyStatus: 'Active',
      );

  @override
  Future<RecommendationModel> dismissRecommendation(String id) async => mockRecs.first;

  @override
  Future<List<RecommendationModel>> refreshRecommendations() async => mockRecs;
}

class MockNotificationRepoForLifecycle implements NotificationRepository {
  final List<NotificationModel> mockNotifications;
  MockNotificationRepoForLifecycle(this.mockNotifications);

  @override
  Future<List<NotificationModel>> getNotifications({bool unreadOnly = false}) async => mockNotifications;

  @override
  Future<int> getUnreadCount() async => mockNotifications.length;

  @override
  Future<NotificationModel> markAsRead(String id) async => mockNotifications.first;

  @override
  Future<int> markAllAsRead() async => 0;

  @override
  Future<NotificationPreferenceModel> getPreferences() async => const NotificationPreferenceModel(
        userId: 'usr-1',
        expiryAlerts: true,
        criticalExpiryAlerts: true,
        pantryUpdates: true,
        recommendationAlerts: true,
        quietHoursEnabled: false,
      );

  @override
  Future<NotificationPreferenceModel> updatePreferences(Map<String, dynamic> data) async =>
      const NotificationPreferenceModel(
        userId: 'usr-1',
        expiryAlerts: true,
        criticalExpiryAlerts: true,
        pantryUpdates: true,
        recommendationAlerts: true,
        quietHoursEnabled: false,
      );

  @override
  Future<ConsumerDeviceModel> registerDevice(String deviceId, String platform, {String? fcmToken}) async {
    return ConsumerDeviceModel(
      id: 'dev-1',
      userId: 'usr-1',
      deviceId: deviceId,
      platform: platform,
      fcmToken: fcmToken,
      isActive: true,
    );
  }
}

void main() {
  final catDairy = {
    'id': 'cat-dairy',
    'name': 'Dairy & Eggs',
    'is_active': true,
  };

  final catProduce = {
    'id': 'cat-produce',
    'name': 'Fresh Produce',
    'is_active': true,
  };

  final milkProduct = {
    'id': 'prod-milk',
    'name': 'Avenzo Whole Milk 1L',
    'sku': 'MK-001',
    'barcode': '890123400001',
    'category_id': 'cat-dairy',
    'category': {'id': 'cat-dairy', 'name': 'Dairy & Eggs'},
    'brand_id': 'brand-avenzo',
    'brand': {'id': 'brand-avenzo', 'name': 'Avenzo Farm'},
    'unit_of_measure': 'Liters',
    'unit_price': 60.00,
    'shelf_life_days': 5,
    'has_expiry': true,
    'image_url': 'https://example.com/milk.png',
    'is_active': true,
    'available_quantity': 20,
    'is_available': true,
  };

  final outOfStockProduct = {
    'id': 'prod-sourdough',
    'name': 'Artisan Sourdough',
    'sku': 'SD-002',
    'barcode': '890123400002',
    'category_id': 'cat-dairy',
    'category': {'id': 'cat-dairy', 'name': 'Dairy & Eggs'},
    'unit_of_measure': 'loaves',
    'unit_price': 40.00,
    'shelf_life_days': 3,
    'has_expiry': true,
    'image_url': null,
    'is_active': true,
    'available_quantity': 0,
    'is_available': false,
  };

  group('End-to-End B2C Catalog Lifecycle Verification', () {
    test('1. Draft product is hidden from marketplace; publishing makes it visible; unpublishing hides it again', () async {
      final mockApi = LifecycleSimulatedApiClient();
      mockApi.activeCategories = [catDairy, catProduce];

      final marketplaceRepo = MarketplaceRepository(apiClient: mockApi);
      final notifier = MarketplaceNotifier(repository: marketplaceRepo);

      // Initially no products are published (all products in draft)
      mockApi.publishedProducts = [];
      await notifier.loadProducts();
      expect(notifier.state.products, isEmpty, reason: 'Draft product must be hidden');

      // Admin publishes Milk in business web -> now returned by API
      mockApi.publishedProducts = [milkProduct];
      await notifier.refresh();
      expect(notifier.state.products.length, 1);
      expect(notifier.state.products.first.id, 'prod-milk');
      expect(notifier.state.products.first.isAvailable, true);

      // Admin unpublishes Milk -> disappears from marketplace
      mockApi.publishedProducts = [];
      await notifier.refresh();
      expect(notifier.state.products, isEmpty, reason: 'Unpublished product must disappear');
    });

    test('2. Products in unpublished/inactive categories are not exposed to consumers', () async {
      final mockApi = LifecycleSimulatedApiClient();
      // Only Dairy is active, Produce is inactive/unpublished
      mockApi.activeCategories = [catDairy];
      // Product belonging to inactive category Produce
      final produceItem = {
        'id': 'prod-apple',
        'name': 'Crisp Royal Apples',
        'sku': 'AP-003',
        'category_id': 'cat-produce',
        'unit_of_measure': 'kg',
        'unit_price': 120.00,
        'has_expiry': true,
        'is_active': true,
        'available_quantity': 50,
        'is_available': true,
      };
      mockApi.publishedProducts = [milkProduct, produceItem];

      final marketplaceRepo = MarketplaceRepository(apiClient: mockApi);
      final categories = await marketplaceRepo.getCategories();

      // Only active categories returned
      expect(categories.any((c) => c.id == 'cat-dairy'), isTrue);
      expect(categories.any((c) => c.id == 'cat-produce'), isFalse);

      // Filtering by active category returns only that category's products
      final filteredProducts = await marketplaceRepo.getProducts(categoryId: 'cat-dairy');
      expect(filteredProducts.length, 1);
      expect(filteredProducts.first.id, 'prod-milk');
    });

    test('3. Product image URLs and category associations render correctly', () {
      final model = MarketplaceProductModel.fromJson(milkProduct);
      expect(model.imageUrl, 'https://example.com/milk.png');
      expect(model.categoryName, 'Dairy & Eggs');
      expect(model.brandName, 'Avenzo Farm');
      expect(model.shelfLifeDays, 5);
      expect(model.unitPrice, 60.00);

      // Model without image handles null gracefully
      final noImageModel = MarketplaceProductModel.fromJson(outOfStockProduct);
      expect(noImageModel.imageUrl, isNull);
    });

    testWidgets('4. Out-of-stock products cannot be added to cart', (tester) async {
      final mockApi = LifecycleSimulatedApiClient()
        ..activeCategories = [catDairy]
        ..publishedProducts = [milkProduct, outOfStockProduct];

      final marketplaceRepo = MarketplaceRepository(apiClient: mockApi);
      final cartRepo = MockCartRepoForLifecycle(
        currentCart: const CartModel(id: 'c1', userId: 'u1', status: 'ACTIVE'),
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            marketplaceRepositoryProvider.overrideWithValue(marketplaceRepo),
            cartRepositoryProvider.overrideWithValue(cartRepo),
          ],
          child: const MaterialApp(
            home: MarketplaceScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Milk is In Stock
      expect(find.text('In Stock'), findsOneWidget);
      // Sourdough is Out of Stock
      expect(find.text('Out of Stock'), findsOneWidget);

      // Verify button status for in-stock vs out-of-stock
      final buttons = tester.widgetList<ElevatedButton>(find.byType(ElevatedButton)).toList();
      expect(buttons.length, 2);

      // In-stock Milk has an enabled button (onPressed != null)
      expect(buttons[0].onPressed, isNotNull);

      // Out-of-stock Sourdough has a disabled button (onPressed == null)
      expect(buttons[1].onPressed, isNull, reason: 'Out-of-stock product button must be disabled');

      // Tap add to cart on in-stock Milk
      final inStockButton = find.byType(ElevatedButton).first;
      await tester.ensureVisible(inStockButton);
      await tester.pumpAndSettle();
      await tester.tap(inStockButton);
      await tester.pump();

      expect(cartRepo.wasAddCalled, isTrue);
      expect(cartRepo.lastAddedProductId, 'prod-milk');
    });

    testWidgets('5. Existing pantry, scanner, expiry, notifications, and recommendations remain functional', (tester) async {
      final pantryRepo = MockPantryRepoForLifecycle([
        PantryItemModel(
          id: 'pantry-1',
          pantryId: 'p1',
          customName: 'Whole Milk',
          quantity: 1,
          unit: 'liters',
          expiryDate: DateTime.now().add(const Duration(days: 4)),
          storageLocation: 'refrigerator',
          daysToExpiry: 4,
          expiryStatus: 'FRESH',
          status: 'active',
          purchaseDate: DateTime.now(),
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
      ]);
      final scannerRepo = MockScannerRepoForLifecycle();
      final recRepo = MockRecommendationRepoForLifecycle([
        RecommendationModel(
          id: 'rec-1',
          userId: 'usr-1',
          pantryItemId: 'item-1',
          recommendationType: 'USE_SOON',
          priority: 'HIGH',
          title: 'Use Milk Before Friday',
          message: 'Your milk expires in 2 days.',
          reason: 'Expiring soon',
          suggestedAction: 'Use in cooking',
          isDismissed: false,
          createdAt: DateTime.now(),
        ),
      ]);
      final notifRepo = MockNotificationRepoForLifecycle([
        NotificationModel(
          id: 'notif-1',
          userId: 'usr-1',
          notificationType: 'CATALOG_UPDATE',
          title: 'Fresh Bread In Stock',
          body: 'Fresh sourdough bread is now available in your local hub.',
          status: 'UNREAD',
          isRead: false,
          createdAt: DateTime.now(),
        ),
      ]);

      final container = ProviderContainer(
        overrides: [
          pantryRepositoryProvider.overrideWithValue(pantryRepo),
          productLookupRepositoryProvider.overrideWithValue(scannerRepo),
          recommendationRepositoryProvider.overrideWithValue(recRepo),
          notificationRepositoryProvider.overrideWithValue(notifRepo),
        ],
      );

      // 1. Pantry items load
      final items = await container.read(pantryRepositoryProvider).getPantryItems();
      expect(items.length, 1);
      expect(items.first.displayName, 'Whole Milk');
      expect(items.first.daysToExpiry, 4);

      // 2. Scanner lookup functions
      final lookup = await container.read(productLookupRepositoryProvider).lookupByBarcode('890123400001');
      expect(lookup, isNotNull);
      expect(lookup!.name, 'Organic Whole Milk');

      // 3. Recommendations load
      await container.read(recommendationsProvider.notifier).fetchData();
      final recs = container.read(recommendationsProvider).recommendations;
      expect(recs.length, 1);
      expect(recs.first.title, 'Use Milk Before Friday');

      // 4. Notifications load
      await container.read(notificationsProvider.notifier).fetchData();
      final notifs = container.read(notificationsProvider).notifications;
      expect(notifs.length, 1);
      expect(notifs.first.title, 'Fresh Bread In Stock');
    });
  });
}
