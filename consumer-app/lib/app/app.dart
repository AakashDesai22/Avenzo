import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/services/fcm_service.dart';
import '../features/auth/providers/auth_provider.dart';
import 'router.dart';
import 'theme/app_theme.dart';

/// AVENZO Consumer App Root Widget
/// Configures Material 3 theme, GoRouter navigation, and FCM auth listener.
class AvenzoApp extends ConsumerWidget {
  const AvenzoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    // Listen to authentication state for FCM device registration lifecycle
    ref.listen<AuthState>(authNotifierProvider, (previous, next) {
      final fcmService = ref.read(fcmServiceProvider);
      if (next is Authenticated) {
        fcmService.initialize().then((_) {
          fcmService.syncDeviceRegistration();
        });
      } else if (next is Unauthenticated) {
        fcmService.unregisterDevice();
      }
    });

    return MaterialApp.router(
      title: 'AVENZO Consumer',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light,
      routerConfig: router,
    );
  }
}
