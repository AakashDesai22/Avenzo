import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import 'notification_models.dart';

/// Repository managing Consumer Notifications API interactions.
class NotificationRepository {
  final ApiClient _apiClient;

  NotificationRepository({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  /// List notifications for authenticated consumer.
  Future<List<NotificationModel>> getNotifications({bool unreadOnly = false}) async {
    try {
      final response = await _apiClient.get(
        '/notifications',
        queryParameters: {'unread_only': unreadOnly},
      );
      final data = response.data;
      if (data is List) {
        return data
            .map((e) => NotificationModel.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return [];
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to fetch notifications: $e');
    }
  }

  /// Get unread notification count.
  Future<int> getUnreadCount() async {
    try {
      final response = await _apiClient.get('/notifications/unread-count');
      final body = response.data as Map<String, dynamic>;
      return body['unread_count'] as int? ?? 0;
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to fetch unread notification count: $e');
    }
  }

  /// Mark notification as read.
  Future<NotificationModel> markAsRead(String notificationId) async {
    try {
      final response = await _apiClient.post('/notifications/$notificationId/read');
      return NotificationModel.fromJson(response.data as Map<String, dynamic>);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to mark notification as read: $e');
    }
  }

  /// Mark all notifications as read.
  Future<int> markAllAsRead() async {
    try {
      final response = await _apiClient.post('/notifications/read-all');
      final body = response.data as Map<String, dynamic>;
      return body['unread_count'] as int? ?? 0;
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to mark all notifications as read: $e');
    }
  }

  /// Get notification preferences.
  Future<NotificationPreferenceModel> getPreferences() async {
    try {
      final response = await _apiClient.get('/notifications/preferences');
      return NotificationPreferenceModel.fromJson(response.data as Map<String, dynamic>);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to fetch notification preferences: $e');
    }
  }

  /// Update notification preferences.
  Future<NotificationPreferenceModel> updatePreferences(Map<String, dynamic> data) async {
    try {
      final response = await _apiClient.put('/notifications/preferences', data: data);
      return NotificationPreferenceModel.fromJson(response.data as Map<String, dynamic>);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to update notification preferences: $e');
    }
  }

  /// Register consumer device token.
  Future<ConsumerDeviceModel> registerDevice(String deviceId, String platform, {String? fcmToken}) async {
    try {
      final response = await _apiClient.post(
        '/notifications/devices',
        data: {
          'device_id': deviceId,
          'platform': platform,
          if (fcmToken != null) 'fcm_token': fcmToken,
        },
      );
      return ConsumerDeviceModel.fromJson(response.data as Map<String, dynamic>);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(message: 'Failed to register consumer device: $e');
    }
  }
}
