import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/shared/models/pantry_item_model.dart';

void main() {
  group('PantryItemModel Recall Tests', () {
    test('PantryItemModel correctly parses recall fields from JSON', () {
      final json = {
        'id': 'pi-101',
        'pantry_id': 'pantry-1',
        'product_id': 'prod-1',
        'product': {
          'id': 'prod-1',
          'name': 'Organic Milk',
          'sku': 'MILK-001',
          'has_expiry': true,
        },
        'batch_id': 'batch-99',
        'batch_number': 'B-MILK-2026-01',
        'order_item_id': 'oi-55',
        'quantity': 2.0,
        'unit': 'L',
        'storage_location': 'fridge',
        'status': 'active',
        'is_recalled': true,
        'recalled_at': '2026-08-26T12:00:00Z',
        'recall_reason': 'Bacterial contamination detected during routine testing.',
        'days_to_expiry': 15,
        'expiry_status': 'SAFE',
        'created_at': '2026-08-20T10:00:00Z',
        'updated_at': '2026-08-26T12:00:00Z',
      };

      final item = PantryItemModel.fromJson(json);

      assert(item.id == 'pi-101');
      assert(item.batchNumber == 'B-MILK-2026-01');
      assert(item.orderItemId == 'oi-55');
      assert(item.isRecalled == true);
      assert(item.recallReason == 'Bacterial contamination detected during routine testing.');
      assert(item.formattedDte == 'RECALLED — DO NOT CONSUME');
    });

    test('PantryItemModel formattedDte displays expiry info when not recalled', () {
      final json = {
        'id': 'pi-102',
        'pantry_id': 'pantry-1',
        'quantity': 1.0,
        'unit': 'units',
        'storage_location': 'pantry',
        'status': 'active',
        'is_recalled': false,
        'days_to_expiry': 3,
        'expiry_status': 'CRITICAL',
        'created_at': '2026-08-20T10:00:00Z',
        'updated_at': '2026-08-20T10:00:00Z',
      };

      final item = PantryItemModel.fromJson(json);

      assert(item.isRecalled == false);
      assert(item.formattedDte == '3 days left');
    });
  });
}
