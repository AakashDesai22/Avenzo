import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/presentation/login_screen.dart';
import '../features/auth/presentation/register_screen.dart';
import '../features/auth/presentation/splash_screen.dart';
import '../features/auth/providers/auth_provider.dart';
import '../features/expiry/presentation/expiry_screen_shell.dart';
import '../features/home/presentation/bottom_nav_shell.dart';
import '../features/home/presentation/home_dashboard_screen.dart';
import '../features/pantry/presentation/pantry_screen.dart';
import '../features/profile/presentation/profile_screen.dart';
import '../features/scanner/presentation/scanner_screen_shell.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'root');

/// GoRouter provider with authentication state listening and route guards
final routerProvider = Provider<GoRouter>((ref) {
  final authNotifier = ref.watch(authNotifierProvider.notifier);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/splash',
    refreshListenable: _ListenableAdapter(authNotifier),
    redirect: (BuildContext context, GoRouterState state) {
      final authState = ref.read(authNotifierProvider);
      final isSplash = state.matchedLocation == '/splash';
      final isLogin = state.matchedLocation == '/login';
      final isRegister = state.matchedLocation == '/register';

      // 1. Loading state: keep user on splash screen
      if (authState is AuthInitial || authState is AuthLoading) {
        return isSplash ? null : '/splash';
      }

      // 2. Unauthenticated or Role Rejected: redirect to login if attempting protected routes
      if (authState is Unauthenticated || authState is AuthRoleRejected) {
        if (isLogin || isRegister) return null;
        return '/login';
      }

      // 3. Authenticated: redirect from auth screens to home dashboard
      if (authState is Authenticated) {
        if (isSplash || isLogin || isRegister) {
          return '/home/dashboard';
        }
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return BottomNavShell(navigationShell: navigationShell);
        },
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/dashboard',
                builder: (context, state) => const HomeDashboardScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/pantry',
                builder: (context, state) => const PantryScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/scan',
                builder: (context, state) => const ScannerScreenShell(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/expiring',
                builder: (context, state) => const ExpiryScreenShell(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/profile',
                builder: (context, state) => const ProfileScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
});

/// Listenable adapter wrapping StateNotifier to allow GoRouter refreshListenable
class _ListenableAdapter extends ChangeNotifier {
  _ListenableAdapter(StateNotifier notifier) {
    notifier.addListener((_) {
      notifyListeners();
    });
  }
}
