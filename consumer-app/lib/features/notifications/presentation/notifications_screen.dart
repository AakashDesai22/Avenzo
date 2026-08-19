import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/notification_provider.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  IconData _getTypeIcon(String type) {
    switch (type.toUpperCase()) {
      case 'EXPIRY_7_DAY':
      case 'EXPIRY_3_DAY':
      case 'EXPIRY_TODAY':
        return Icons.timer_outlined;
      case 'PRODUCT_EXPIRED':
        return Icons.warning_amber_rounded;
      case 'PANTRY_UPDATE':
        return Icons.kitchen_outlined;
      case 'RECOMMENDATION':
        return Icons.auto_awesome;
      case 'SYSTEM':
      default:
        return Icons.notifications_none;
    }
  }

  Color _getTypeColor(String type) {
    switch (type.toUpperCase()) {
      case 'EXPIRY_TODAY':
      case 'PRODUCT_EXPIRED':
        return Colors.red.shade700;
      case 'EXPIRY_3_DAY':
        return Colors.orange.shade800;
      case 'RECOMMENDATION':
        return Colors.indigo.shade700;
      default:
        return Colors.blue.shade700;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(notificationsProvider);
    final notifier = ref.read(notificationsProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          if (state.unreadCount > 0)
            TextButton.icon(
              onPressed: () => notifier.markAllAsRead(),
              icon: const Icon(Icons.done_all, size: 18),
              label: const Text('Mark all read'),
            ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => context.push('/notifications/preferences'),
            tooltip: 'Notification Settings',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => notifier.fetchData(),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            children: [
              if (state.isLoading)
                const Padding(
                  padding: EdgeInsets.all(40.0),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (state.errorMessage != null)
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Card(
                    color: Colors.red.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        children: [
                          Icon(Icons.error_outline, color: Colors.red.shade700, size: 36),
                          const SizedBox(height: 8),
                          Text(state.errorMessage!, textAlign: TextAlign.center),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: () => notifier.fetchData(),
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    ),
                  ),
                )
              else if (state.notifications.isEmpty)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 64),
                    child: Column(
                      children: [
                        Icon(Icons.notifications_off_outlined, size: 64, color: Colors.grey.shade400),
                        const SizedBox(height: 16),
                        const Text(
                          'No Notifications',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'You\'re all caught up! Expiry alerts and updates will appear here.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey.shade700),
                        ),
                      ],
                    ),
                  ),
                )
              else
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: state.notifications.length,
                  separatorBuilder: (context, index) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final item = state.notifications[index];
                    final color = _getTypeColor(item.notificationType);
                    final icon = _getTypeIcon(item.notificationType);

                    return ListTile(
                      tileColor: item.isRead ? Colors.transparent : Colors.blue.shade50.withAlpha(80),
                      leading: CircleAvatar(
                        backgroundColor: color.withAlpha(30),
                        child: Icon(icon, color: color, size: 22),
                      ),
                      title: Row(
                        children: [
                          Expanded(
                            child: Text(
                              item.title,
                              style: TextStyle(
                                fontWeight: item.isRead ? FontWeight.normal : FontWeight.bold,
                              ),
                            ),
                          ),
                          if (!item.isRead)
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: Colors.blue,
                                shape: BoxShape.circle,
                              ),
                            ),
                        ],
                      ),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 4),
                          Text(item.body),
                          const SizedBox(height: 4),
                          Text(
                            _formatDate(item.createdAt),
                            style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                          ),
                        ],
                      ),
                      onTap: () {
                        if (!item.isRead) {
                          notifier.markAsRead(item.id);
                        }
                      },
                    );
                  },
                ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}
