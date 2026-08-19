import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/features/scanner/data/product_lookup_repository.dart';
import 'package:avenzo_consumer/features/scanner/providers/scanner_provider.dart';
import 'package:avenzo_consumer/features/scanner/presentation/scanned_product_confirmation_sheet.dart';

class MockProductLookupRepository extends ProductLookupRepository {
  final Map<String, ProductMasterModel> mockDatabase;
  bool shouldThrow;

  MockProductLookupRepository({
    required this.mockDatabase,
    this.shouldThrow = false,
  });

  @override
  Future<ProductMasterModel?> lookupByBarcode(String barcode) async {
    if (shouldThrow) throw Exception('API Network Failure');
    final clean = ProductLookupRepository.normalizeBarcode(barcode);
    return mockDatabase[clean];
  }
}

void main() {
  final sampleProduct = const ProductMasterModel(
    id: 'prod-890123',
    name: 'Organic Whole Milk 1L',
    sku: 'MILK-ORG-1L',
    barcode: '8901234567890',
    brandName: 'Amul',
    categoryName: 'Dairy',
    unitOfMeasure: 'liters',
    shelfLifeDays: 7,
  );

  group('Barcode Normalization & Basic Repository Tests', () {
    test('1 & 2. Barcode normalization trims whitespace and preserves leading zeros', () {
      expect(ProductLookupRepository.normalizeBarcode('  00890123456  '), equals('00890123456'));
      expect(ProductLookupRepository.normalizeBarcode(''), equals(''));
      expect(ProductLookupRepository.normalizeBarcode('   '), equals(''));
    });

    test('4. Successful product lookup returns ProductMasterModel', () async {
      final mockRepo = MockProductLookupRepository(mockDatabase: {
        '8901234567890': sampleProduct,
      });

      final result = await mockRepo.lookupByBarcode('  8901234567890  ');
      expect(result, isNotNull);
      expect(result!.id, equals('prod-890123'));
      expect(result.name, equals('Organic Whole Milk 1L'));
      expect(result.brandName, equals('Amul'));
      expect(result.unitOfMeasure, equals('liters'));
    });

    test('5. Product not found returns null', () async {
      final mockRepo = MockProductLookupRepository(mockDatabase: {});
      final result = await mockRepo.lookupByBarcode('9999999999999');
      expect(result, isNull);
    });
  });

  group('ScannerNotifier State Transition Tests', () {
    test('3 & 7. State transitions from Initial -> LookingUp -> ProductFound', () async {
      final mockRepo = MockProductLookupRepository(mockDatabase: {
        '8901234567890': sampleProduct,
      });
      final container = ProviderContainer(
        overrides: [
          productLookupRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );

      final notifier = container.read(scannerNotifierProvider.notifier);
      expect(container.read(scannerNotifierProvider), isA<ScannerInitial>());

      final future = notifier.processBarcode('8901234567890');
      expect(container.read(scannerNotifierProvider), isA<ScannerLookingUp>());

      await future;

      final finalState = container.read(scannerNotifierProvider);
      expect(finalState, isA<ScannerProductFound>());
      final found = finalState as ScannerProductFound;
      expect(found.product.name, equals('Organic Whole Milk 1L'));

      // Test reset
      notifier.resetScanner();
      expect(container.read(scannerNotifierProvider), isA<ScannerInitial>());
    });

    test('5. State transitions to ScannerProductNotFound when barcode missing', () async {
      final mockRepo = MockProductLookupRepository(mockDatabase: {});
      final container = ProviderContainer(
        overrides: [
          productLookupRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );

      final notifier = container.read(scannerNotifierProvider.notifier);
      await notifier.processBarcode('0000000000000');

      final finalState = container.read(scannerNotifierProvider);
      expect(finalState, isA<ScannerProductNotFound>());
      expect((finalState as ScannerProductNotFound).barcode, equals('0000000000000'));
    });

    test('6. State transitions to ScannerError on network failure', () async {
      final mockRepo = MockProductLookupRepository(mockDatabase: {}, shouldThrow: true);
      final container = ProviderContainer(
        overrides: [
          productLookupRepositoryProvider.overrideWithValue(mockRepo),
        ],
      );

      final notifier = container.read(scannerNotifierProvider.notifier);
      await notifier.processBarcode('8901234567890');

      final finalState = container.read(scannerNotifierProvider);
      expect(finalState, isA<ScannerError>());
    });
  });

  group('ScannedProductConfirmationSheet Widget Tests', () {
    testWidgets('9 & 10. Confirmation sheet displays product details and Add to Pantry button', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: ScannedProductConfirmationSheet(product: sampleProduct),
            ),
          ),
        ),
      );

      expect(find.text('Product Matched!'), findsOneWidget);
      expect(find.text('Organic Whole Milk 1L'), findsOneWidget);
      expect(find.text('Amul'), findsOneWidget);
      expect(find.text('Dairy'), findsOneWidget);
      expect(find.text('8901234567890'), findsOneWidget);
      expect(find.text('Add to Digital Pantry'), findsOneWidget);
    });
  });
}
