import 'package:flutter/foundation.dart';

@immutable
class NotificationModel {
  final String id;
  final String userId;
  final String notificationType; // EXPIRY_7_DAY, EXPIRY_3_DAY, EXPIRY_TODAY, PRODUCT_EXPIRED, PANTRY_UPDATE, RECOMMENDATION, SYSTEM
  final String title;
  final String body;
  final String? payloadJson;
  final String status; // CREATED, SCHEDULED, SENT, DELIVERED, READ, FAILED
  final bool isRead;
  final DateTime? readAt;
  final DateTime createdAt;

  const NotificationModel({
    required this.id,
    required this.userId,
    required this.notificationType,
    required this.title,
    required this.body,
    this.payloadJson,
    required this.status,
    required this.isRead,
    this.readAt,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      notificationType: json['notification_type'] as String? ?? 'SYSTEM',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      payloadJson: json['payload_json'] as String?,
      status: json['status'] as String? ?? 'CREATED',
      isRead: json['is_read'] as bool? ?? false,
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at'] as String) : null,
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at'] as String) : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'notification_type': notificationType,
      'title': title,
      'body': body,
      'payload_json': payloadJson,
      'status': status,
      'is_read': isRead,
      'read_at': readAt?.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
    };
  }
}

@immutable
class NotificationPreferenceModel {
  final String userId;
  final bool expiryAlerts;
  final bool criticalExpiryAlerts;
  final bool pantryUpdates;
  final bool recommendationAlerts;
  final bool quietHoursEnabled;
  final String? quietHoursStart;
  final String? quietHoursEnd;

  const NotificationPreferenceModel({
    required this.userId,
    required this.expiryAlerts,
    required this.criticalExpiryAlerts,
    required this.pantryUpdates,
    required this.recommendationAlerts,
    required this.quietHoursEnabled,
    this.quietHoursStart,
    this.quietHoursEnd,
  });

  factory NotificationPreferenceModel.fromJson(Map<String, dynamic> json) {
    return NotificationPreferenceModel(
      userId: json['user_id'] as String? ?? '',
      expiryAlerts: json['expiry_alerts'] as bool? ?? true,
      criticalExpiryAlerts: json['critical_expiry_alerts'] as bool? ?? true,
      pantryUpdates: json['pantry_updates'] as bool? ?? true,
      recommendationAlerts: json['recommendation_alerts'] as bool? ?? true,
      quietHoursEnabled: json['quiet_hours_enabled'] as bool? ?? false,
      quietHoursStart: json['quiet_hours_start'] as String? ?? '22:00',
      quietHoursEnd: json['quiet_hours_end'] as String? ?? '07:00',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'expiry_alerts': expiryAlerts,
      'critical_expiry_alerts': criticalExpiryAlerts,
      'pantry_updates': pantryUpdates,
      'recommendation_alerts': recommendationAlerts,
      'quiet_hours_enabled': quietHoursEnabled,
      'quiet_hours_start': quietHoursStart,
      'quiet_hours_end': quietHoursEnd,
    };
  }
}

@immutable
class ConsumerDeviceModel {
  final String id;
  final String userId;
  final String deviceId;
  final String platform;
  final String? fcmToken;
  final bool isActive;

  const ConsumerDeviceModel({
    required this.id,
    required this.userId,
    required this.deviceId,
    required this.platform,
    this.fcmToken,
    required this.isActive,
  });

  factory ConsumerDeviceModel.fromJson(Map<String, dynamic> json) {
    return ConsumerDeviceModel(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      deviceId: json['device_id'] as String,
      platform: json['platform'] as String? ?? 'android',
      fcmToken: json['fcm_token'] as String?,
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}
