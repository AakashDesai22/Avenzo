import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/features/notifications/data/notification_models.dart';
import 'package:avenzo_consumer/features/notifications/data/notification_repository.dart';
import 'package:avenzo_consumer/features/notifications/providers/notification_provider.dart';
import 'package:avenzo_consumer/features/notifications/presentation/notifications_screen.dart';
import 'package:avenzo_consumer/features/notifications/presentation/notification_preferences_screen.dart';

class MockNotificationRepository implements NotificationRepository {
  final List<NotificationModel> mockNotifications;
  final NotificationPreferenceModel mockPreferences;
  int unreadCount;

  MockNotificationRepository({
    required this.mockNotifications,
    required this.mockPreferences,
    this.unreadCount = 1,
  });

  @override
  Future<List<NotificationModel>> getNotifications({bool unreadOnly = false}) async {
    return mockNotifications;
  }

  @override
  Future<int> getUnreadCount() async => unreadCount;

  @override
  Future<NotificationModel> markAsRead(String notificationId) async {
    unreadCount = unreadCount > 0 ? unreadCount - 1 : 0;
    final item = mockNotifications.firstWhere((n) => n.id == notificationId);
    return NotificationModel(
      id: item.id,
      userId: item.userId,
      notificationType: item.notificationType,
      title: item.title,
      body: item.body,
      status: 'READ',
      isRead: true,
      createdAt: item.createdAt,
    );
  }

  @override
  Future<int> markAllAsRead() async {
    unreadCount = 0;
    return 0;
  }

  @override
  Future<NotificationPreferenceModel> getPreferences() async => mockPreferences;

  @override
  Future<NotificationPreferenceModel> updatePreferences(Map<String, dynamic> data) async {
    return NotificationPreferenceModel(
      userId: mockPreferences.userId,
      expiryAlerts: data['expiry_alerts'] as bool? ?? mockPreferences.expiryAlerts,
      criticalExpiryAlerts: data['critical_expiry_alerts'] as bool? ?? mockPreferences.criticalExpiryAlerts,
      pantryUpdates: data['pantry_updates'] as bool? ?? mockPreferences.pantryUpdates,
      recommendationAlerts: data['recommendation_alerts'] as bool? ?? mockPreferences.recommendationAlerts,
      quietHoursEnabled: data['quiet_hours_enabled'] as bool? ?? mockPreferences.quietHoursEnabled,
      quietHoursStart: data['quiet_hours_start'] as String? ?? mockPreferences.quietHoursStart,
      quietHoursEnd: data['quiet_hours_end'] as String? ?? mockPreferences.quietHoursEnd,
    );
  }

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
  final sampleNotification = NotificationModel(
    id: 'notif-1',
    userId: 'user-1',
    notificationType: 'EXPIRY_3_DAY',
    title: 'Milk Expiring Soon',
    body: 'Your milk expires in 3 days.',
    status: 'CREATED',
    isRead: false,
    createdAt: DateTime.now(),
  );

  final samplePrefs = const NotificationPreferenceModel(
    userId: 'user-1',
    expiryAlerts: true,
    criticalExpiryAlerts: true,
    pantryUpdates: true,
    recommendationAlerts: true,
    quietHoursEnabled: false,
  );

  group('Notification Models Unit Tests', () {
    test('NotificationModel.fromJson parses correctly', () {
      final json = {
        'id': 'n-123',
        'user_id': 'u-456',
        'notification_type': 'PRODUCT_EXPIRED',
        'title': 'Bread Expired',
        'body': 'Your bread expired today.',
        'status': 'SENT',
        'is_read': false,
        'created_at': '2026-08-19T10:00:00.000Z',
      };

      final model = NotificationModel.fromJson(json);

      expect(model.id, equals('n-123'));
      expect(model.notificationType, equals('PRODUCT_EXPIRED'));
      expect(model.title, equals('Bread Expired'));
      expect(model.isRead, isFalse);
    });

    test('NotificationPreferenceModel.fromJson parses correctly', () {
      final json = {
        'user_id': 'u-100',
        'expiry_alerts': true,
        'critical_expiry_alerts': true,
        'pantry_updates': false,
        'recommendation_alerts': true,
        'quiet_hours_enabled': true,
        'quiet_hours_start': '23:00',
        'quiet_hours_end': '06:00',
      };

      final prefs = NotificationPreferenceModel.fromJson(json);

      expect(prefs.pantryUpdates, isFalse);
      expect(prefs.quietHoursEnabled, isTrue);
      expect(prefs.quietHoursStart, equals('23:00'));
    });
  });

  group('NotificationsNotifier State Tests', () {
    test('fetchData populates state with notifications, unread count, and preferences', () async {
      final mockRepo = MockNotificationRepository(
        mockNotifications: [sampleNotification],
        mockPreferences: samplePrefs,
        unreadCount: 1,
      );

      final notifier = NotificationsNotifier(mockRepo);
      await notifier.fetchData();

      expect(notifier.state.isLoading, isFalse);
      expect(notifier.state.notifications.length, equals(1));
      expect(notifier.state.unreadCount, equals(1));
      expect(notifier.state.preferences?.expiryAlerts, isTrue);
    });

    test('markAsRead updates item status and reduces unread count', () async {
      final mockRepo = MockNotificationRepository(
        mockNotifications: [sampleNotification],
        mockPreferences: samplePrefs,
        unreadCount: 1,
      );

      final notifier = NotificationsNotifier(mockRepo);
      await notifier.fetchData();

      await notifier.markAsRead('notif-1');

      expect(notifier.state.unreadCount, equals(0));
      expect(notifier.state.notifications.first.isRead, isTrue);
    });
  });

  group('Notification Widgets Tests', () {
    testWidgets('NotificationsScreen renders list and title', (WidgetTester tester) async {
      final mockRepo = MockNotificationRepository(
        mockNotifications: [sampleNotification],
        mockPreferences: samplePrefs,
        unreadCount: 1,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            notificationRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const MaterialApp(
            home: NotificationsScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Notifications'), findsOneWidget);
      expect(find.text('Milk Expiring Soon'), findsOneWidget);
      expect(find.text('Your milk expires in 3 days.'), findsOneWidget);
    });

    testWidgets('NotificationPreferencesScreen renders switch tiles', (WidgetTester tester) async {
      final mockRepo = MockNotificationRepository(
        mockNotifications: [sampleNotification],
        mockPreferences: samplePrefs,
        unreadCount: 0,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            notificationRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const MaterialApp(
            home: NotificationPreferencesScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Notification Settings'), findsOneWidget);
      expect(find.text('Expiry Alerts'), findsOneWidget);
      expect(find.text('Critical Expiry Alerts'), findsOneWidget);
      expect(find.text('Pantry Updates'), findsOneWidget);
    });
  });
}
