import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/shared/models/pantry_item_model.dart';
import 'package:avenzo_consumer/features/pantry/data/pantry_repository.dart';
import 'package:avenzo_consumer/features/pantry/providers/pantry_provider.dart';
import 'package:avenzo_consumer/features/pantry/presentation/pantry_screen.dart';

class MockPantryRepository extends PantryRepository {
  final List<PantryItemModel> mockItems;
  bool shouldFail;

  MockPantryRepository({
    required this.mockItems,
    this.shouldFail = false,
  });

  @override
  Future<List<PantryItemModel>> getPantryItems({String? storageLocation, String status = 'active'}) async {
    if (shouldFail) throw Exception('Network Error');
    if (storageLocation != null && storageLocation.isNotEmpty) {
      return mockItems.where((i) => i.storageLocation == storageLocation).toList();
    }
    return mockItems;
  }

  @override
  Future<PantryItemModel> addPantryItem({
    String? productId,
    String? batchId,
    String? customName,
    String? barcode,
    required double quantity,
    required String unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    required String storageLocation,
    String? notes,
  }) async {
    if (shouldFail) throw Exception('Add Failed');
    final newItem = PantryItemModel(
      id: 'p-new',
      pantryId: 'pantry-1',
      customName: customName ?? 'New Item',
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
      status: 'active',
      expiryStatus: 'SAFE',
      daysToExpiry: 10,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
    mockItems.add(newItem);
    return newItem;
  }

  @override
  Future<PantryItemModel> consumeItem(String id, double quantity) async {
    final index = mockItems.indexWhere((i) => i.id == id);
    if (index == -1) throw Exception('Item not found');
    final item = mockItems[index];
    final newQty = item.quantity - quantity;
    final updated = item.copyWith(
      quantity: newQty > 0 ? newQty : 0,
      status: newQty <= 0 ? 'consumed' : 'active',
    );
    mockItems[index] = updated;
    return updated;
  }

  @override
  Future<PantryItemModel> discardItem(String id, double quantity) async {
    final index = mockItems.indexWhere((i) => i.id == id);
    if (index == -1) throw Exception('Item not found');
    final item = mockItems[index];
    final newQty = item.quantity - quantity;
    final updated = item.copyWith(
      quantity: newQty > 0 ? newQty : 0,
      status: newQty <= 0 ? 'discarded' : 'active',
    );
    mockItems[index] = updated;
    return updated;
  }

  @override
  Future<PantryItemModel> deletePantryItem(String id) async {
    mockItems.removeWhere((i) => i.id == id);
    return PantryItemModel(
      id: id,
      pantryId: 'pantry-1',
      quantity: 0,
      unit: 'units',
      storageLocation: 'pantry',
      status: 'deleted',
      expiryStatus: 'N/A',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }
}

void main() {
  final sampleItem1 = PantryItemModel(
    id: 'p1',
    pantryId: 'pantry-1',
    customName: 'Organic Milk 1L',
    quantity: 2.0,
    unit: 'liters',
    storageLocation: 'fridge',
    status: 'active',
    daysToExpiry: 5,
    expiryStatus: 'EXPIRING_SOON',
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  final sampleItem2 = PantryItemModel(
    id: 'p2',
    pantryId: 'pantry-1',
    customName: 'Whole Wheat Bread',
    quantity: 1.0,
    unit: 'loaf',
    storageLocation: 'pantry',
    status: 'active',
    daysToExpiry: -1,
    expiryStatus: 'EXPIRED',
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  group('PantryItemModel JSON Parsing & Helper Tests', () {
    test('PantryItemModel parses JSON correctly', () {
      final json = {
        'id': 'item-100',
        'pantry_id': 'pantry-abc',
        'custom_name': 'Almond Butter',
        'barcode': '8901234567890',
        'quantity': 3.5,
        'unit': 'jars',
        'storage_location': 'pantry',
        'status': 'active',
        'days_to_expiry': 12,
        'expiry_status': 'SAFE',
        'created_at': '2026-08-19T20:00:00.000Z',
        'updated_at': '2026-08-19T20:00:00.000Z',
      };

      final model = PantryItemModel.fromJson(json);
      expect(model.id, equals('item-100'));
      expect(model.displayName, equals('Almond Butter'));
      expect(model.quantity, equals(3.5));
      expect(model.storageLocation, equals('pantry'));
      expect(model.daysToExpiry, equals(12));
      expect(model.formattedDte, equals('12 days left'));
    });

    test('Formatted DTE helper handles different expiry states', () {
      final itemSafe = sampleItem1.copyWith(daysToExpiry: 10, expiryStatus: 'SAFE');
      expect(itemSafe.formattedDte, equals('10 days left'));

      final itemToday = sampleItem1.copyWith(daysToExpiry: 0, expiryStatus: 'CRITICAL');
      expect(itemToday.formattedDte, equals('Expires today'));

      final item1Day = sampleItem1.copyWith(daysToExpiry: 1, expiryStatus: 'CRITICAL');
      expect(item1Day.formattedDte, equals('1 day left'));

      final itemExpired = sampleItem2;
      expect(itemExpired.formattedDte, equals('Expired 1 day ago'));

      final itemNoExpiry = sampleItem1.copyWith(daysToExpiry: null, expiryStatus: 'N/A');
      expect(itemNoExpiry.formattedDte, equals('No expiry'));
    });
  });

  group('PantryNotifier State Management Tests', () {
    test('PantryNotifier fetches items and updates state to PantryLoaded', () async {
      final mockRepo = MockPantryRepository(mockItems: [sampleItem1, sampleItem2]);
      final container = ProviderContainer(
        overrides: [
          pantryRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );

      final notifier = container.read(pantryNotifierProvider.notifier);
      expect(container.read(pantryNotifierProvider), isA<PantryInitial>());

      await notifier.fetchPantryItems();

      final state = container.read(pantryNotifierProvider);
      expect(state, isA<PantryLoaded>());
      final loaded = state as PantryLoaded;
      expect(loaded.items.length, equals(2));
    });

    test('PantryNotifier handles error gracefully', () async {
      final mockRepo = MockPantryRepository(mockItems: [], shouldFail: true);
      final container = ProviderContainer(
        overrides: [
          pantryRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );

      final notifier = container.read(pantryNotifierProvider.notifier);
      await notifier.fetchPantryItems();

      final state = container.read(pantryNotifierProvider);
      expect(state, isA<PantryError>());
    });

    test('PantryNotifier handles consumeItem mutation', () async {
      final mockRepo = MockPantryRepository(mockItems: [sampleItem1]);
      final container = ProviderContainer(
        overrides: [
          pantryRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );

      final notifier = container.read(pantryNotifierProvider.notifier);
      await notifier.fetchPantryItems();

      // Consume 1.0 out of 2.0
      final success = await notifier.consumeItem('p1', 1.0);
      expect(success, isTrue);

      final loaded = container.read(pantryNotifierProvider) as PantryLoaded;
      expect(loaded.items.first.quantity, equals(1.0));
      expect(loaded.items.first.status, equals('active'));

      // Consume remaining 1.0
      await notifier.consumeItem('p1', 1.0);
      final finalLoaded = container.read(pantryNotifierProvider) as PantryLoaded;
      expect(finalLoaded.items.length, equals(0)); // Removed from active list
    });

    test('PantryNotifier handles deleteItem mutation', () async {
      final mockRepo = MockPantryRepository(mockItems: [sampleItem1, sampleItem2]);
      final container = ProviderContainer(
        overrides: [
          pantryRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );

      final notifier = container.read(pantryNotifierProvider.notifier);
      await notifier.fetchPantryItems();

      final success = await notifier.deleteItem('p1');
      expect(success, isTrue);

      final loaded = container.read(pantryNotifierProvider) as PantryLoaded;
      expect(loaded.items.length, equals(1));
      expect(loaded.items.first.id, equals('p2'));
    });
  });

  group('PantryScreen Widget Tests', () {
    testWidgets('PantryScreen renders loaded items and expiry badges', (WidgetTester tester) async {
      final mockRepo = MockPantryRepository(mockItems: [sampleItem1, sampleItem2]);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            pantryRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const MaterialApp(
            home: PantryScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('My Digital Pantry'), findsOneWidget);
      expect(find.text('Organic Milk 1L'), findsOneWidget);
      expect(find.text('Whole Wheat Bread'), findsOneWidget);
      expect(find.text('5 days left'), findsOneWidget);
      expect(find.text('Expired 1 day ago'), findsOneWidget);
    });

    testWidgets('PantryScreen renders empty state when no items exist', (WidgetTester tester) async {
      final mockRepo = MockPantryRepository(mockItems: []);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            pantryRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const MaterialApp(
            home: PantryScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Your Pantry is Empty'), findsOneWidget);
      expect(find.text('Add First Item'), findsOneWidget);
    });
  });
}
