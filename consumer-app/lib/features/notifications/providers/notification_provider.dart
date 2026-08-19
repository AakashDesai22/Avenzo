import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/notification_models.dart';
import '../data/notification_repository.dart';

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  return NotificationRepository();
});

class NotificationsState {
  final bool isLoading;
  final List<NotificationModel> notifications;
  final int unreadCount;
  final NotificationPreferenceModel? preferences;
  final String? errorMessage;

  const NotificationsState({
    this.isLoading = false,
    this.notifications = const [],
    this.unreadCount = 0,
    this.preferences,
    this.errorMessage,
  });

  NotificationsState copyWith({
    bool? isLoading,
    List<NotificationModel>? notifications,
    int? unreadCount,
    NotificationPreferenceModel? preferences,
    String? errorMessage,
  }) {
    return NotificationsState(
      isLoading: isLoading ?? this.isLoading,
      notifications: notifications ?? this.notifications,
      unreadCount: unreadCount ?? this.unreadCount,
      preferences: preferences ?? this.preferences,
      errorMessage: errorMessage,
    );
  }
}

class NotificationsNotifier extends StateNotifier<NotificationsState> {
  final NotificationRepository _repository;

  NotificationsNotifier(this._repository) : super(const NotificationsState()) {
    fetchData();
  }

  Future<void> fetchData() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final results = await Future.wait([
        _repository.getNotifications(),
        _repository.getUnreadCount(),
        _repository.getPreferences(),
      ]);

      final recs = results[0] as List<NotificationModel>;
      final unread = results[1] as int;
      final prefs = results[2] as NotificationPreferenceModel;

      state = state.copyWith(
        isLoading: false,
        notifications: recs,
        unreadCount: unread,
        preferences: prefs,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }

  Future<void> markAsRead(String notificationId) async {
    final updatedList = state.notifications.map((n) {
      if (n.id == notificationId) {
        return NotificationModel(
          id: n.id,
          userId: n.userId,
          notificationType: n.notificationType,
          title: n.title,
          body: n.body,
          payloadJson: n.payloadJson,
          status: 'READ',
          isRead: true,
          readAt: DateTime.now(),
          createdAt: n.createdAt,
        );
      }
      return n;
    }).toList();

    final newUnread = (state.unreadCount > 0) ? state.unreadCount - 1 : 0;
    state = state.copyWith(notifications: updatedList, unreadCount: newUnread);

    try {
      await _repository.markAsRead(notificationId);
    } catch (e) {
      fetchData();
    }
  }

  Future<void> markAllAsRead() async {
    final updatedList = state.notifications.map((n) {
      return NotificationModel(
        id: n.id,
        userId: n.userId,
        notificationType: n.notificationType,
        title: n.title,
        body: n.body,
        payloadJson: n.payloadJson,
        status: 'READ',
        isRead: true,
        readAt: DateTime.now(),
        createdAt: n.createdAt,
      );
    }).toList();

    state = state.copyWith(notifications: updatedList, unreadCount: 0);

    try {
      await _repository.markAllAsRead();
    } catch (e) {
      fetchData();
    }
  }

  Future<void> updatePreferences(Map<String, dynamic> updates) async {
    try {
      final updatedPrefs = await _repository.updatePreferences(updates);
      state = state.copyWith(preferences: updatedPrefs);
    } catch (e) {
      state = state.copyWith(
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }
}

final notificationsProvider =
    StateNotifierProvider<NotificationsNotifier, NotificationsState>((ref) {
  final repo = ref.watch(notificationRepositoryProvider);
  return NotificationsNotifier(repo);
});

final unreadNotificationCountProvider = Provider<int>((ref) {
  return ref.watch(notificationsProvider).unreadCount;
});
