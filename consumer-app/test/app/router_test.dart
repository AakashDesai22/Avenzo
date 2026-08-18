import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/app/router.dart';
import 'package:avenzo_consumer/features/auth/providers/auth_provider.dart';
import 'package:avenzo_consumer/features/auth/data/auth_repository.dart';
import 'package:avenzo_consumer/shared/models/user_model.dart';

class MockAuthRepoForRouter extends AuthRepository {
  bool hasTokenResult = false;
  UserModel? userToReturn;

  @override
  Future<bool> hasToken() async => hasTokenResult;

  @override
  Future<UserModel> getCurrentUser() async {
    if (userToReturn != null) return userToReturn!;
    throw Exception('No user');
  }

  @override
  Future<void> logout() async {}
}

void main() {
  final consumerUser = UserModel(
    id: 'u1',
    email: 'test@consumer.com',
    firstName: 'Test',
    lastName: 'Consumer',
    roleId: 'r1',
    role: const RoleModel(id: 'r1', name: 'CONSUMER'),
    userType: 'consumer',
    isActive: true,
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  testWidgets('Router redirects Unauthenticated user from protected routes to /login', (WidgetTester tester) async {
    final mockRepo = MockAuthRepoForRouter()..hasTokenResult = false;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(mockRepo),
        ],
        child: Consumer(
          builder: (context, ref, child) {
            final router = ref.watch(routerProvider);
            return MaterialApp.router(
              routerConfig: router,
            );
          },
        ),
      ),
    );

    // Initial pump initializes router at /splash -> checks auth -> redirects to /login
    await tester.pumpAndSettle();

    expect(find.text('Sign In'), findsOneWidget);
  });

  testWidgets('Router redirects Authenticated Consumer to /home/dashboard', (WidgetTester tester) async {
    final mockRepo = MockAuthRepoForRouter()
      ..hasTokenResult = true
      ..userToReturn = consumerUser;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(mockRepo),
        ],
        child: Consumer(
          builder: (context, ref, child) {
            final router = ref.watch(routerProvider);
            return MaterialApp.router(
              routerConfig: router,
            );
          },
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Hello, Test 👋'), findsOneWidget);
    expect(find.text('Quick Actions'), findsOneWidget);
  });
}
