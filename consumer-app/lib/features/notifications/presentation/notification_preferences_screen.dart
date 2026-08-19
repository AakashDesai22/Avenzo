import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/notification_provider.dart';

class NotificationPreferencesScreen extends ConsumerWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(notificationsProvider);
    final notifier = ref.read(notificationsProvider.notifier);
    final prefs = state.preferences;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notification Settings', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: prefs == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              children: [
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
                  child: Text(
                    'Alert Preferences',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.indigo,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                SwitchListTile(
                  title: const Text('Expiry Alerts'),
                  subtitle: const Text('Receive notifications for items approaching expiration'),
                  value: prefs.expiryAlerts,
                  onChanged: (val) {
                    notifier.updatePreferences({'expiry_alerts': val});
                  },
                ),
                const Divider(height: 1),
                SwitchListTile(
                  title: const Text('Critical Expiry Alerts'),
                  subtitle: const Text('Urgent alerts for items expiring today or tomorrow'),
                  value: prefs.criticalExpiryAlerts,
                  onChanged: (val) {
                    notifier.updatePreferences({'critical_expiry_alerts': val});
                  },
                ),
                const Divider(height: 1),
                SwitchListTile(
                  title: const Text('Pantry Updates'),
                  subtitle: const Text('Notifications when pantry items are updated'),
                  value: prefs.pantryUpdates,
                  onChanged: (val) {
                    notifier.updatePreferences({'pantry_updates': val});
                  },
                ),
                const Divider(height: 1),
                SwitchListTile(
                  title: const Text('Smart Recommendations'),
                  subtitle: const Text('Personalized insights & waste-reduction tips'),
                  value: prefs.recommendationAlerts,
                  onChanged: (val) {
                    notifier.updatePreferences({'recommendation_alerts': val});
                  },
                ),
                const Divider(height: 1),

                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 24, 16, 8),
                  child: Text(
                    'Quiet Hours',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.indigo,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                SwitchListTile(
                  title: const Text('Enable Quiet Hours'),
                  subtitle: Text(
                    prefs.quietHoursEnabled
                        ? 'Muted between ${prefs.quietHoursStart} and ${prefs.quietHoursEnd}'
                        : 'Mute non-critical notifications during night hours',
                  ),
                  value: prefs.quietHoursEnabled,
                  onChanged: (val) {
                    notifier.updatePreferences({'quiet_hours_enabled': val});
                  },
                ),
              ],
            ),
    );
  }
}
