import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/features/home/presentation/home_dashboard_screen.dart';
import 'package:avenzo_consumer/features/auth/data/auth_repository.dart';
import 'package:avenzo_consumer/features/auth/providers/auth_provider.dart';
import 'package:avenzo_consumer/features/marketplace/data/marketplace_repository.dart';
import 'package:avenzo_consumer/features/marketplace/domain/marketplace_product_model.dart';
import 'package:avenzo_consumer/features/cart/data/cart_repository.dart';
import 'package:avenzo_consumer/features/cart/domain/cart_model.dart';
import 'package:avenzo_consumer/core/network/api_client.dart';
import 'package:avenzo_consumer/shared/models/user_model.dart';
import 'package:dio/dio.dart';

class MockApiClientForHome extends ApiClient {
  List<Map<String, dynamic>> products = [];
  List<Map<String, dynamic>> categories = [];

  MockApiClientForHome() : super(customDio: Dio());

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
        data: {'success': true, 'data': categories} as T,
      );
    }
    return Response<T>(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'success': true, 'data': products} as T,
    );
  }
}

class MockCartRepositoryForHome extends CartRepository {
  CartModel cartData;
  bool wasAddItemCalled = false;

  MockCartRepositoryForHome({required this.cartData})
      : super(apiClient: MockApiClientForHome());

  @override
  Future<CartModel> getCart() async => cartData;

  @override
  Future<CartModel> addItem({required String productId, int quantity = 1}) async {
    wasAddItemCalled = true;
    return cartData;
  }
}

class MockAuthRepoForHome extends AuthRepository {
  final UserModel user;
  MockAuthRepoForHome(this.user);

  @override
  Future<bool> hasToken() async => true;

  @override
  Future<UserModel> getCurrentUser() async => user;

  @override
  Future<void> logout() async {}
}

void main() {
  final testUser = UserModel(
    id: 'u-101',
    email: 'consumer@avenzo.dev',
    firstName: 'Priya',
    lastName: 'Sharma',
    roleId: 'r-consumer',
    role: const RoleModel(id: 'r-consumer', name: 'CONSUMER'),
    userType: 'consumer',
    isActive: true,
    createdAt: DateTime(2026, 1, 1),
    updatedAt: DateTime(2026, 1, 1),
  );

  final testCategories = [
    {
      'id': 'cat-dairy',
      'name': 'Dairy & Eggs',
      'is_active': true,
      'created_at': '2026-10-20T10:00:00Z',
    },
    {
      'id': 'cat-produce',
      'name': 'Fresh Produce',
      'is_active': true,
      'created_at': '2026-10-20T10:00:00Z',
    },
  ];

  final testInStockProduct = {
    'id': 'prod-milk-1',
    'name': 'Fresh Whole Milk 1L',
    'description': 'Pasteurized whole cow milk',
    'sku': 'MILK-1L',
    'barcode': '8901001',
    'category_id': 'cat-dairy',
    'category': {'id': 'cat-dairy', 'name': 'Dairy & Eggs'},
    'brand_id': null,
    'brand': null,
    'unit_of_measure': '1 Liter',
    'unit_price': 62.00,
    'shelf_life_days': 5,
    'has_expiry': true,
    'image_url': null,
    'is_active': true,
    'available_quantity': 15,
    'is_available': true,
  };

  final testOutOfStockProduct = {
    'id': 'prod-bread-2',
    'name': 'Multigrain Artisan Bread',
    'description': 'Zero preservatives',
    'sku': 'BREAD-MG',
    'barcode': '8901002',
    'category_id': 'cat-produce',
    'category': {'id': 'cat-produce', 'name': 'Fresh Produce'},
    'brand_id': null,
    'brand': null,
    'unit_of_measure': '400g loaf',
    'unit_price': 48.00,
    'shelf_life_days': 3,
    'has_expiry': true,
    'image_url': null,
    'is_active': true,
    'available_quantity': 0,
    'is_available': false,
  };

  Widget createHomeScreen({
    required MockApiClientForHome mockApi,
    required MockCartRepositoryForHome mockCartRepo,
  }) {
    final marketplaceRepo = MarketplaceRepository(apiClient: mockApi);
    final authRepo = MockAuthRepoForHome(testUser);

    return ProviderScope(
      overrides: [
        authRepositoryProvider.overrideWithValue(authRepo),
        marketplaceRepositoryProvider.overrideWithValue(marketplaceRepo),
        cartRepositoryProvider.overrideWithValue(mockCartRepo),
      ],
      child: const MaterialApp(
        home: HomeDashboardScreen(),
      ),
    );
  }

  group('HomeDashboardScreen Quick Commerce Suite', () {
    testWidgets('Renders header with brand, delivery location, and search bar', (tester) async {
      final mockApi = MockApiClientForHome();
      final mockCart = MockCartRepositoryForHome(
        cartData: const CartModel(id: 'c1', userId: 'u1', status: 'ACTIVE'),
      );

      await tester.pumpWidget(createHomeScreen(mockApi: mockApi, mockCartRepo: mockCart));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Brand & Delivery location
      expect(find.text('AVENZO'), findsOneWidget);
      expect(find.textContaining('Deliver to Home'), findsOneWidget);

      // Search bar placeholder
      expect(find.textContaining('Search fresh groceries'), findsOneWidget);

      // Core action icons
      expect(find.byIcon(Icons.analytics_outlined), findsOneWidget);
      expect(find.byIcon(Icons.notifications_outlined), findsOneWidget);
      expect(find.byIcon(Icons.person_outline_rounded), findsOneWidget);
    });

    testWidgets('Renders dynamic categories row from backend with All option', (tester) async {
      final mockApi = MockApiClientForHome()..categories = testCategories;
      final mockCart = MockCartRepositoryForHome(
        cartData: const CartModel(id: 'c1', userId: 'u1', status: 'ACTIVE'),
      );

      await tester.pumpWidget(createHomeScreen(mockApi: mockApi, mockCartRepo: mockCart));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));

      // Category Section Title
      expect(find.text('Shop by Category'), findsOneWidget);
      expect(find.text('See All'), findsWidgets);

      // Category chips
      expect(find.text('All'), findsOneWidget);
      expect(find.text('Dairy & Eggs'), findsWidgets);
      expect(find.text('Fresh Produce'), findsWidgets);
    });

    testWidgets('Renders genuine AVENZO purpose banner and quick expiry actions', (tester) async {
      final mockApi = MockApiClientForHome();
      final mockCart = MockCartRepositoryForHome(
        cartData: const CartModel(id: 'c1', userId: 'u1', status: 'ACTIVE'),
      );

      await tester.pumpWidget(createHomeScreen(mockApi: mockApi, mockCartRepo: mockCart));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Purpose banner
      expect(find.text('Fresh Groceries with Guaranteed Shelf Life'), findsOneWidget);
      expect(find.text('ZERO WASTE • SMART LIFECYCLE'), findsOneWidget);

      // Expiry quick actions
      expect(find.text('Scan Product'), findsOneWidget);
      expect(find.text('My Pantry'), findsOneWidget);
      expect(find.text('Expiring Soon'), findsOneWidget);

      // Smart Insights
      expect(find.text('Smart Insights & Recommendations'), findsOneWidget);
    });

    testWidgets('Renders live product cards in Explore Products shelf with Add button', (tester) async {
      final mockApi = MockApiClientForHome()
        ..categories = testCategories
        ..products = [testInStockProduct, testOutOfStockProduct];
      final mockCart = MockCartRepositoryForHome(
        cartData: const CartModel(id: 'c1', userId: 'u1', status: 'ACTIVE'),
      );

      await tester.pumpWidget(createHomeScreen(mockApi: mockApi, mockCartRepo: mockCart));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Explore Products shelf
      expect(find.text('Explore Products'), findsOneWidget);

      // In-stock product card
      expect(find.text('Fresh Whole Milk 1L'), findsWidgets);
      expect(find.text('1 Liter'), findsWidgets);
      expect(find.text('5d shelf life'), findsWidgets);
      expect(find.text('+ ADD'), findsWidgets);

      // Out-of-stock product card
      expect(find.text('Multigrain Artisan Bread'), findsWidgets);
      expect(find.text('Out of Stock'), findsWidgets);
      expect(find.text('Unavailable'), findsWidgets);
    });

    testWidgets('Tapping + ADD calls cart repository and triggers feedback', (tester) async {
      final mockApi = MockApiClientForHome()
        ..categories = testCategories
        ..products = [testInStockProduct];
      final mockCart = MockCartRepositoryForHome(
        cartData: const CartModel(id: 'c1', userId: 'u1', status: 'ACTIVE'),
      );

      await tester.pumpWidget(createHomeScreen(mockApi: mockApi, mockCartRepo: mockCart));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Find + ADD button and tap it
      final addButton = find.text('+ ADD').first;
      await tester.ensureVisible(addButton);
      await tester.pump();
      await tester.tap(addButton);
      await tester.pump();

      expect(mockCart.wasAddItemCalled, isTrue);
      expect(find.textContaining('added to cart'), findsOneWidget);

      // Dismiss snackbar timer
      await tester.pump(const Duration(seconds: 5));
    });

    testWidgets('Floating cart bar displays when cart has items and hides when empty', (tester) async {
      final mockApi = MockApiClientForHome();

      // Case 1: Empty cart -> no floating cart bar
      final emptyCart = MockCartRepositoryForHome(
        cartData: const CartModel(id: 'c1', userId: 'u1', status: 'ACTIVE', items: []),
      );
      await tester.pumpWidget(createHomeScreen(mockApi: mockApi, mockCartRepo: emptyCart));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.text('View Cart'), findsNothing);

      // Case 2: Cart with items -> floating cart bar visible
      final populatedCart = MockCartRepositoryForHome(
        cartData: CartModel(
          id: 'c1',
          userId: 'u1',
          status: 'ACTIVE',
          totalItemsCount: 3,
          calculatedSubtotal: 186.00,
          items: [
            CartItemModel(
              id: 'item-1',
              cartId: 'c1',
              productId: 'prod-milk-1',
              quantity: 3,
              product: MarketplaceProductModel.fromJson(testInStockProduct),
            ),
          ],
        ),
      );

      await tester.pumpWidget(createHomeScreen(mockApi: mockApi, mockCartRepo: populatedCart));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));

      expect(find.text('View Cart'), findsOneWidget);
      expect(find.text('3 items in cart'), findsOneWidget);
      expect(find.text('₹186.00'), findsOneWidget);
    });
  });
}
