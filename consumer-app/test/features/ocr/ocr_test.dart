import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/features/ocr/data/ocr_models.dart';
import 'package:avenzo_consumer/features/ocr/data/receipt_line_parser.dart';
import 'package:avenzo_consumer/features/ocr/data/receipt_product_matcher.dart';
import 'package:avenzo_consumer/features/ocr/providers/ocr_provider.dart';
import 'package:avenzo_consumer/features/scanner/data/product_lookup_repository.dart';
import 'package:avenzo_consumer/features/pantry/data/pantry_repository.dart';
import 'package:avenzo_consumer/features/pantry/providers/pantry_provider.dart';
import 'package:avenzo_consumer/shared/models/pantry_item_model.dart';
import 'package:avenzo_consumer/features/ocr/presentation/receipt_review_screen.dart';

class MockPantryRepoForOcr extends PantryRepository {
  final List<PantryItemModel> addedItems = [];

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
    final item = PantryItemModel(
      id: 'pantry-${addedItems.length + 1}',
      pantryId: 'pantry-1',
      customName: customName ?? 'Item',
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
      status: 'active',
      expiryStatus: 'SAFE',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
    addedItems.add(item);
    return item;
  }
}

void main() {
  const sampleRawReceiptText = '''
FRESH SUPERMARKET
TEL: 123-456-7890
DATE: 2026-08-19

2x Organic Whole Milk 1L  \$7.50
Whole Wheat Bread         \$3.20
SUBTOTAL                  \$10.70
TAX                       \$0.80
TOTAL                     \$11.50
THANK YOU FOR SHOPPING WITH US
''';

  final sampleCatalog = [
    const ProductMasterModel(
      id: 'prod-milk',
      name: 'Organic Whole Milk 1L',
      sku: 'MILK-1L',
      unitOfMeasure: 'liters',
    ),
    const ProductMasterModel(
      id: 'prod-bread',
      name: 'Whole Wheat Bread',
      sku: 'BREAD-1',
      unitOfMeasure: 'loaf',
    ),
  ];

  group('ReceiptLineParser Tests', () {
    test('4, 5, 6, 7, 8. Parser filters noise lines and extracts items, prices, quantities', () {
      final result = ReceiptLineParser.parseText(sampleRawReceiptText);

      expect(result.merchantName, equals('FRESH SUPERMARKET'));
      expect(result.totalAmount, equals(11.50));
      expect(result.items.length, equals(2));

      final milk = result.items[0];
      expect(milk.normalizedName, contains('Organic Whole Milk 1L'));
      expect(milk.quantity, equals(2.0));
      expect(milk.totalPrice, equals(7.50));

      final bread = result.items[1];
      expect(bread.normalizedName, contains('Whole Wheat Bread'));
      expect(bread.quantity, equals(1.0));
      expect(bread.totalPrice, equals(3.20));
    });

    test('Noise line detection filters store footers and totals', () {
      expect(ReceiptLineParser.isNoiseLine('SUBTOTAL \$10.00'), isTrue);
      expect(ReceiptLineParser.isNoiseLine('TOTAL \$11.50'), isTrue);
      expect(ReceiptLineParser.isNoiseLine('THANK YOU'), isTrue);
      expect(ReceiptLineParser.isNoiseLine('Organic Whole Milk 1L \$7.50'), isFalse);
    });
  });

  group('ReceiptProductMatcher Tests', () {
    test('9, 10, 11. Matches items against Product Master catalog', () {
      final parsed = ReceiptLineParser.parseText(sampleRawReceiptText);
      final matched = ReceiptProductMatcher.matchItems(parsed.items, sampleCatalog);

      expect(matched[0].matchStatus, equals('MATCHED'));
      expect(matched[0].matchedProductId, equals('prod-milk'));

      expect(matched[1].matchStatus, equals('MATCHED'));
      expect(matched[1].matchedProductId, equals('prod-bread'));
    });

    test('Unmatched items marked as UNMATCHED', () {
      final item = const ReceiptOcrItem(
        id: 'o1',
        rawName: 'Exotic Dragonfruit',
        normalizedName: 'Exotic Dragonfruit',
        quantity: 1.0,
      );
      final result = ReceiptProductMatcher.matchItems([item], sampleCatalog);
      expect(result.first.matchStatus, equals('UNMATCHED'));
    });
  });

  group('OcrNotifier State Management & Pantry Ingestion Tests', () {
    test('13, 14, 15, 16, 17, 21. Manages selection, item updates, and ingests to PantryNotifier', () async {
      final parsed = ReceiptLineParser.parseText(sampleRawReceiptText);
      final container = ProviderContainer();
      final notifier = container.read(ocrNotifierProvider.notifier);

      // Force state to OcrReviewReady
      notifier.addItemManually(parsed.items.first);
      final state = container.read(ocrNotifierProvider);
      expect(state, isA<OcrReviewReady>());

      // Test item quantity update
      notifier.updateItemQuantity(parsed.items.first.id, 3.0);
      final updatedState = container.read(ocrNotifierProvider) as OcrReviewReady;
      expect(updatedState.result.items.first.quantity, equals(3.0));

      // Test ingestion to pantry
      final mockPantryRepo = MockPantryRepoForOcr();
      final pantryNotifier = PantryNotifier(repository: mockPantryRepo);

      final success = await notifier.ingestSelectedItemsToPantry(
        pantryNotifier,
        storageLocation: 'fridge',
      );

      expect(success, isTrue);
      expect(mockPantryRepo.addedItems.length, equals(1));
      expect(mockPantryRepo.addedItems.first.storageLocation, equals('fridge'));
    });
  });

  group('ReceiptReviewScreen Widget Tests', () {
    testWidgets('13, 14. ReceiptReviewScreen renders extracted items and ingestion CTA button', (WidgetTester tester) async {
      final parsed = ReceiptLineParser.parseText(sampleRawReceiptText);

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: ReceiptReviewScreen(result: parsed),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Review Scanned Receipt'), findsOneWidget);
      expect(find.text('FRESH SUPERMARKET'), findsOneWidget);
      expect(find.text('Total: \$11.50'), findsOneWidget);
      expect(find.text('Add 2 Items to Pantry'), findsOneWidget);
    });
  });
}
