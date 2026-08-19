import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/app/router.dart';
import 'package:avenzo_consumer/features/auth/providers/auth_provider.dart';
import 'package:avenzo_consumer/features/auth/data/auth_repository.dart';
import 'package:avenzo_consumer/shared/models/user_model.dart';

import 'package:avenzo_consumer/features/pantry/data/pantry_repository.dart';
import 'package:avenzo_consumer/features/pantry/providers/pantry_provider.dart';
import 'package:avenzo_consumer/shared/models/pantry_item_model.dart';

class MockAuthRepoForHomeShell extends AuthRepository {
  final UserModel user;
  MockAuthRepoForHomeShell(this.user);

  @override
  Future<bool> hasToken() async => true;

  @override
  Future<UserModel> getCurrentUser() async => user;

  @override
  Future<void> logout() async {}
}

class MockPantryRepoForHomeShell extends PantryRepository {
  @override
  Future<List<PantryItemModel>> getPantryItems({String? storageLocation, String status = 'active'}) async {
    return [];
  }
}

void main() {
  final consumerUser = UserModel(
    id: 'u1',
    email: 'test@consumer.com',
    firstName: 'Aakash',
    lastName: 'Desai',
    roleId: 'r1',
    role: const RoleModel(id: 'r1', name: 'CONSUMER'),
    userType: 'consumer',
    isActive: true,
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  testWidgets('BottomNavShell renders 5 navigation items and switches tabs', (WidgetTester tester) async {
    final mockRepo = MockAuthRepoForHomeShell(consumerUser);
    final mockPantryRepo = MockPantryRepoForHomeShell();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(mockRepo),
          pantryRepositoryProvider.overrideWithValue(mockPantryRepo),
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

    // Verify 5 navigation bar destinations exist
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('My Pantry'), findsWidgets);
    expect(find.text('Scan'), findsWidgets);
    expect(find.text('Expiring'), findsWidgets);
    expect(find.text('Profile'), findsWidgets);

    // Tap on My Pantry tab in bottom nav bar
    await tester.tap(find.byIcon(Icons.kitchen_outlined));
    await tester.pumpAndSettle();

    expect(find.text('My Digital Pantry'), findsOneWidget);

    // Tap on Expiring tab
    await tester.tap(find.byIcon(Icons.timer_outlined));
    await tester.pumpAndSettle();

    expect(find.text('Personal Expiry Tracking'), findsOneWidget);

    // Tap on Profile tab
    await tester.tap(find.byIcon(Icons.person_outline));
    await tester.pumpAndSettle();

    expect(find.text('Aakash Desai'), findsOneWidget);
    expect(find.text('Sign Out'), findsOneWidget);
  });
}
