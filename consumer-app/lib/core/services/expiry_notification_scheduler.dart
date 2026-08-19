import '../../shared/models/pantry_item_model.dart';
import 'notification_service.dart';

/// Service responsible for calculating, scheduling, canceling, and synchronizing
/// local device expiry alert notifications for consumer pantry items.
class ExpiryNotificationScheduler {
  final NotificationService _notificationService;

  ExpiryNotificationScheduler({
    NotificationService? notificationService,
  }) : _notificationService = notificationService ?? NotificationService();

  /// Deterministic ID generator creating stable 32-bit integer IDs for a pantry item.
  /// Offset: 1 = 7-day warning, 2 = 3-day warning, 3 = expiry-day warning
  static int generateNotificationId(String pantryItemId, int offset) {
    final baseHash = pantryItemId.hashCode.abs() % 1000000;
    return (baseHash * 10) + offset;
  }

  /// Cancels all scheduled notification events (7-day, 3-day, 0-day) for a specific pantry item.
  Future<void> cancelItemNotifications(String pantryItemId) async {
    final id7Day = generateNotificationId(pantryItemId, 1);
    final id3Day = generateNotificationId(pantryItemId, 2);
    final id0Day = generateNotificationId(pantryItemId, 3);

    await _notificationService.cancelNotification(id7Day);
    await _notificationService.cancelNotification(id3Day);
    await _notificationService.cancelNotification(id0Day);
  }

  /// Synchronizes scheduled local notifications with current list of pantry items.
  /// Idempotent: cancels previous item notifications and schedules only future valid alerts.
  Future<void> syncExpiryNotifications(
    List<PantryItemModel> items, {
    DateTime? nowOverride,
  }) async {
    final now = nowOverride ?? DateTime.now();

    for (final item in items) {
      // 1. If item is inactive, consumed, discarded, zero-quantity, or has no expiry: cancel notifications
      if (item.status != 'active' || item.quantity <= 0 || item.expiryDate == null) {
        await cancelItemNotifications(item.id);
        continue;
      }

      // 2. Item is active with valid expiry date: calculate 7-day, 3-day, and 0-day target times
      final expDate = item.expiryDate!;
      final date7Day = DateTime(expDate.year, expDate.month, expDate.day, 9, 0).subtract(const Duration(days: 7));
      final date3Day = DateTime(expDate.year, expDate.month, expDate.day, 9, 0).subtract(const Duration(days: 3));
      final date0Day = DateTime(expDate.year, expDate.month, expDate.day, 9, 0);

      // Cancel previous notifications for item before rescheduling
      await cancelItemNotifications(item.id);

      // Schedule 7-day warning if in the future
      if (date7Day.isAfter(now)) {
        await _notificationService.scheduleNotification(
          id: generateNotificationId(item.id, 1),
          title: 'Expiry Reminder',
          body: '${item.displayName} expires in 7 days. Plan to use it soon.',
          scheduledDate: date7Day,
          payload: item.id,
        );
      }

      // Schedule 3-day warning if in the future
      if (date3Day.isAfter(now)) {
        await _notificationService.scheduleNotification(
          id: generateNotificationId(item.id, 2),
          title: 'Expiry Alert',
          body: '${item.displayName} expires in 3 days. Consider using it soon.',
          scheduledDate: date3Day,
          payload: item.id,
        );
      }

      // Schedule Expiry-day warning if in the future
      if (date0Day.isAfter(now)) {
        await _notificationService.scheduleNotification(
          id: generateNotificationId(item.id, 3),
          title: 'Expires Today',
          body: '${item.displayName} expires today. Use it before it goes to waste.',
          scheduledDate: date0Day,
          payload: item.id,
        );
      }
    }
  }
}
