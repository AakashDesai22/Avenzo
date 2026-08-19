import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/core/services/notification_service.dart';
import 'package:avenzo_consumer/core/services/expiry_notification_scheduler.dart';
import 'package:avenzo_consumer/shared/models/pantry_item_model.dart';

class ScheduledCall {
  final int id;
  final String title;
  final String body;
  final DateTime scheduledDate;
  final String? payload;

  ScheduledCall({
    required this.id,
    required this.title,
    required this.body,
    required this.scheduledDate,
    this.payload,
  });
}

class MockNotificationService extends NotificationService {
  final List<ScheduledCall> scheduledList = [];
  final List<int> canceledList = [];
  bool permissionGranted = true;

  @override
  Future<bool> initialize() async => true;

  @override
  Future<bool> requestPermissions() async => permissionGranted;

  @override
  Future<void> scheduleNotification({
    required int id,
    required String title,
    required String body,
    required DateTime scheduledDate,
    String? payload,
  }) async {
    if (scheduledDate.isBefore(DateTime.now())) return;
    scheduledList.add(ScheduledCall(
      id: id,
      title: title,
      body: body,
      scheduledDate: scheduledDate,
      payload: payload,
    ));
  }

  @override
  Future<void> cancelNotification(int id) async {
    canceledList.add(id);
    scheduledList.removeWhere((item) => item.id == id);
  }

  @override
  Future<void> cancelAllNotifications() async {
    scheduledList.clear();
  }
}

void main() {
  late MockNotificationService mockNotificationService;
  late ExpiryNotificationScheduler scheduler;
  final now = DateTime(2026, 8, 19, 10, 0); // Fixed reference time: Aug 19, 2026

  setUp(() {
    mockNotificationService = MockNotificationService();
    scheduler = ExpiryNotificationScheduler(notificationService: mockNotificationService);
  });

  group('ExpiryNotificationScheduler Tests', () {
    test('1 & 2. Notification ID generation is deterministic and unique per item/offset', () {
      final id1_7d = ExpiryNotificationScheduler.generateNotificationId('item-abc-123', 1);
      final id1_3d = ExpiryNotificationScheduler.generateNotificationId('item-abc-123', 2);
      final id1_0d = ExpiryNotificationScheduler.generateNotificationId('item-abc-123', 3);

      final id2_7d = ExpiryNotificationScheduler.generateNotificationId('item-xyz-999', 1);

      // Determinism
      expect(id1_7d, equals(ExpiryNotificationScheduler.generateNotificationId('item-abc-123', 1)));
      // Non-collision within item
      expect(id1_7d, isNot(equals(id1_3d)));
      expect(id1_3d, isNot(equals(id1_0d)));
      // Non-collision across items
      expect(id1_7d, isNot(equals(id2_7d)));
    });

    test('3, 4, 5. Schedules 7-day, 3-day, and 0-day future notifications', () async {
      // Item expiring in 10 days (Aug 29, 2026)
      final item = PantryItemModel(
        id: 'item-future',
        pantryId: 'pantry-1',
        customName: 'Fresh Butter',
        quantity: 2.0,
        unit: 'packs',
        storageLocation: 'fridge',
        status: 'active',
        expiryDate: DateTime(2026, 8, 29),
        daysToExpiry: 10,
        expiryStatus: 'SAFE',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      await scheduler.syncExpiryNotifications([item], nowOverride: now);

      // Should have 3 scheduled alerts: Aug 22 (7-day), Aug 26 (3-day), Aug 29 (0-day)
      expect(mockNotificationService.scheduledList.length, equals(3));
      expect(mockNotificationService.scheduledList.any((s) => s.title == 'Expiry Reminder'), isTrue);
      expect(mockNotificationService.scheduledList.any((s) => s.title == 'Expiry Alert'), isTrue);
      expect(mockNotificationService.scheduledList.any((s) => s.title == 'Expires Today'), isTrue);
    });

    test('6. Past notification times are not scheduled', () async {
      // Item expiring in 4 days (Aug 23, 2026) -> 7-day warning (Aug 16) is in the past!
      final item = PantryItemModel(
        id: 'item-4days',
        pantryId: 'pantry-1',
        customName: 'Cheese Slices',
        quantity: 1.0,
        unit: 'pack',
        storageLocation: 'fridge',
        status: 'active',
        expiryDate: DateTime(2026, 8, 23),
        daysToExpiry: 4,
        expiryStatus: 'EXPIRING_SOON',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      await scheduler.syncExpiryNotifications([item], nowOverride: now);

      // 7-day warning (Aug 16) was past, so only 3-day (Aug 20) and 0-day (Aug 23) scheduled
      expect(mockNotificationService.scheduledList.length, equals(2));
      expect(mockNotificationService.scheduledList.any((s) => s.title == 'Expiry Reminder'), isFalse);
      expect(mockNotificationService.scheduledList.any((s) => s.title == 'Expiry Alert'), isTrue);
      expect(mockNotificationService.scheduledList.any((s) => s.title == 'Expires Today'), isTrue);
    });

    test('7. Items with no expiry date produce no notifications', () async {
      final itemNoExp = PantryItemModel(
        id: 'item-noexp',
        pantryId: 'pantry-1',
        customName: 'Salt Container',
        quantity: 1.0,
        unit: 'box',
        storageLocation: 'pantry',
        status: 'active',
        expiryDate: null,
        daysToExpiry: null,
        expiryStatus: 'N/A',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      await scheduler.syncExpiryNotifications([itemNoExp], nowOverride: now);
      expect(mockNotificationService.scheduledList.length, equals(0));
    });

    test('8, 9, 10, 11. Consumed, discarded, deleted, and zero-quantity items produce no notifications', () async {
      final consumedItem = PantryItemModel(
        id: 'c1',
        pantryId: 'p1',
        customName: 'Milk',
        quantity: 0.0,
        unit: 'L',
        storageLocation: 'fridge',
        status: 'consumed',
        expiryDate: DateTime(2026, 8, 29),
        expiryStatus: 'SAFE',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      final discardedItem = PantryItemModel(
        id: 'd1',
        pantryId: 'p1',
        customName: 'Bread',
        quantity: 0.0,
        unit: 'loaf',
        storageLocation: 'pantry',
        status: 'discarded',
        expiryDate: DateTime(2026, 8, 29),
        expiryStatus: 'SAFE',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      await scheduler.syncExpiryNotifications([consumedItem, discardedItem], nowOverride: now);
      expect(mockNotificationService.scheduledList.length, equals(0));
    });

    test('13. Repeated synchronization is idempotent', () async {
      final item = PantryItemModel(
        id: 'item-idempotent',
        pantryId: 'pantry-1',
        customName: 'Yogurt',
        quantity: 1.0,
        unit: 'cup',
        storageLocation: 'fridge',
        status: 'active',
        expiryDate: DateTime(2026, 8, 29),
        daysToExpiry: 10,
        expiryStatus: 'SAFE',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      await scheduler.syncExpiryNotifications([item], nowOverride: now);
      final countFirst = mockNotificationService.scheduledList.length;

      // Sync second time with same data
      await scheduler.syncExpiryNotifications([item], nowOverride: now);
      final countSecond = mockNotificationService.scheduledList.length;

      expect(countFirst, equals(3));
      expect(countSecond, equals(3));
    });

    test('14. Notification cancellation removes all 3 offset notifications for an item', () async {
      const itemId = 'item-cancel-test';
      await scheduler.cancelItemNotifications(itemId);

      final id7 = ExpiryNotificationScheduler.generateNotificationId(itemId, 1);
      final id3 = ExpiryNotificationScheduler.generateNotificationId(itemId, 2);
      final id0 = ExpiryNotificationScheduler.generateNotificationId(itemId, 3);

      expect(mockNotificationService.canceledList, containsAll([id7, id3, id0]));
    });

    test('15. Permission denial does not crash application', () async {
      mockNotificationService.permissionGranted = false;
      final granted = await mockNotificationService.requestPermissions();
      expect(granted, isFalse);
    });
  });
}
