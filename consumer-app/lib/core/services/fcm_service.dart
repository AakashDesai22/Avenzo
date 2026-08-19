import 'dart:io';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/notifications/data/notification_repository.dart';
import '../../features/notifications/providers/notification_provider.dart';
import '../../firebase_options.dart';
import 'notification_service.dart';

/// Top-level background handler for FCM messages.
/// Required to be a top-level function annotated with `@pragma('vm:entry-point')`.
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
    debugPrint(
      '[FCM Background] Message received: ${message.messageId} | Title: ${message.notification?.title}',
    );
  } catch (e) {
    debugPrint('[FCM Background Error] $e');
  }
}

/// Service wrapping Firebase Cloud Messaging (FCM) functionality,
/// token management, permissions, device registration, and message listening.
class FCMService {
  final FirebaseMessaging? _messaging;
  final NotificationRepository _notificationRepository;
  final NotificationService _notificationService;

  String? _currentToken;
  bool _isInitialized = false;

  FCMService({
    FirebaseMessaging? messaging,
    NotificationRepository? notificationRepository,
    NotificationService? notificationService,
  })  : _messaging = messaging,
        _notificationRepository = notificationRepository ?? NotificationRepository(),
        _notificationService = notificationService ?? NotificationService();

  FirebaseMessaging get _messagingInstance => _messaging ?? FirebaseMessaging.instance;

  String? get currentToken => _currentToken;
  bool get isInitialized => _isInitialized;

  /// Initialize FCM listeners and request notification permissions safely.
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      // 1. Request notification permissions
      final settings = await _messagingInstance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );

      debugPrint('[FCM] Permission status: ${settings.authorizationStatus}');

      if (settings.authorizationStatus == AuthorizationStatus.denied) {
        debugPrint('[FCM] Notification permissions denied by user.');
        _isInitialized = true;
        return false;
      }

      // 2. Obtain FCM registration token
      try {
        _currentToken = await _messagingInstance.getToken();
        debugPrint(
          '[FCM] Token acquired: ${_currentToken != null ? "${_currentToken!.substring(0, 10)}..." : "null"}',
        );
      } catch (tokenError) {
        debugPrint('[FCM Warning] Failed to acquire FCM token: $tokenError');
      }

      // 3. Listen for token refresh events
      _messagingInstance.onTokenRefresh.listen((newToken) {
        _currentToken = newToken;
        debugPrint(
          '[FCM] Token refreshed: ${newToken.length > 10 ? newToken.substring(0, 10) : newToken}...',
        );
        syncDeviceRegistration();
      });

      // 4. Listen for foreground notifications
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        debugPrint(
          '[FCM Foreground] Message received: ${message.notification?.title}',
        );
        _handleForegroundMessage(message);
      });

      _isInitialized = true;
      return true;
    } catch (e) {
      debugPrint('[FCM Service Error] $e');
      _isInitialized = false;
      return false;
    }
  }

  /// Handles incoming foreground messages by displaying a local notification using Phase 5C NotificationService.
  void _handleForegroundMessage(RemoteMessage message) {
    final notification = message.notification;
    if (notification != null && notification.title != null) {
      final notificationId = (message.messageId.hashCode).abs();
      _notificationService.showNotification(
        id: notificationId,
        title: notification.title!,
        body: notification.body ?? '',
        payload: message.data.toString(),
      );
    }
  }

  /// Synchronize device token registration with backend for authenticated user.
  Future<void> syncDeviceRegistration() async {
    if (_currentToken == null || _currentToken!.isEmpty) return;

    try {
      final deviceId = await _getOrCreateDeviceId();
      final platform = kIsWeb
          ? 'web'
          : Platform.isIOS
              ? 'ios'
              : 'android';

      await _notificationRepository.registerDevice(
        deviceId,
        platform,
        fcmToken: _currentToken,
      );
      debugPrint(
        '[FCM] Device token registered with backend (DeviceId: $deviceId, Platform: $platform)',
      );
    } catch (e) {
      debugPrint('[FCM Sync Warning] Failed to register device: $e');
    }
  }

  /// Deactivates/Unregisters device on user logout.
  Future<void> unregisterDevice() async {
    try {
      final deviceId = await _getOrCreateDeviceId();
      debugPrint('[FCM] Deactivating device token on logout (DeviceId: $deviceId)');
    } catch (e) {
      debugPrint('[FCM Unregister Error] $e');
    }
  }

  /// Generates or retrieves a persistent stable device ID stored in SharedPreferences.
  Future<String> _getOrCreateDeviceId() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      String? deviceId = prefs.getString('avenzo_device_id');
      if (deviceId == null || deviceId.isEmpty) {
        final now = DateTime.now().millisecondsSinceEpoch;
        deviceId = 'dev_$now';
        await prefs.setString('avenzo_device_id', deviceId);
      }
      return deviceId;
    } catch (e) {
      return 'dev_fallback_1001';
    }
  }
}

/// Provider for FCMService instance.
final fcmServiceProvider = Provider<FCMService>((ref) {
  final repository = ref.watch(notificationRepositoryProvider);
  return FCMService(notificationRepository: repository);
});
