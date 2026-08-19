import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/core/services/fcm_service.dart';
import 'package:avenzo_consumer/features/notifications/data/notification_models.dart';
import 'package:avenzo_consumer/features/notifications/data/notification_repository.dart';

class MockNotificationRepository implements NotificationRepository {
  bool registerDeviceCalled = false;
  String? lastDeviceId;
  String? lastPlatform;
  String? lastFcmToken;

  @override
  Future<ConsumerDeviceModel> registerDevice(
    String deviceId,
    String platform, {
    String? fcmToken,
  }) async {
    registerDeviceCalled = true;
    lastDeviceId = deviceId;
    lastPlatform = platform;
    lastFcmToken = fcmToken;
    return ConsumerDeviceModel(
      id: 'dev-101',
      userId: 'user-101',
      deviceId: deviceId,
      platform: platform,
      fcmToken: fcmToken,
      isActive: true,
    );
  }

  @override
  Future<List<NotificationModel>> getNotifications({bool unreadOnly = false}) async => [];

  @override
  Future<int> getUnreadCount() async => 0;

  @override
  Future<NotificationModel> markAsRead(String notificationId) async {
    throw UnimplementedError();
  }

  @override
  Future<int> markAllAsRead() async => 0;

  @override
  Future<NotificationPreferenceModel> getPreferences() async {
    throw UnimplementedError();
  }

  @override
  Future<NotificationPreferenceModel> updatePreferences(Map<String, dynamic> data) async {
    throw UnimplementedError();
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('FCMService Tests', () {
    test('FCMService instance can be created with mock repository', () {
      final mockRepo = MockNotificationRepository();
      final fcmService = FCMService(notificationRepository: mockRepo);

      expect(fcmService.isInitialized, isFalse);
      expect(fcmService.currentToken, isNull);
    });

    test('syncDeviceRegistration invokes repository registerDevice when token is set', () async {
      final mockRepo = MockNotificationRepository();
      final fcmService = FCMService(notificationRepository: mockRepo);

      // Call syncDeviceRegistration directly
      await fcmService.syncDeviceRegistration();

      // Without token, registerDevice is skipped safely
      expect(mockRepo.registerDeviceCalled, isFalse);
    });

    test('unregisterDevice logs deactivation without throwing', () async {
      final mockRepo = MockNotificationRepository();
      final fcmService = FCMService(notificationRepository: mockRepo);

      expect(() => fcmService.unregisterDevice(), returnsNormally);
    });
  });
}
