import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/features/auth/data/auth_repository.dart';
import 'package:avenzo_consumer/features/auth/providers/auth_provider.dart';
import 'package:avenzo_consumer/shared/models/user_model.dart';

class MockAuthRepository extends AuthRepository {
  bool hasTokenResult = false;
  UserModel? mockUser;
  bool loginShouldFail = false;
  bool logoutCalled = false;

  @override
  Future<bool> hasToken() async => hasTokenResult;

  @override
  Future<UserModel> getCurrentUser() async {
    if (mockUser != null) return mockUser!;
    throw Exception('User not found');
  }

  @override
  Future<AuthTokenResult> login({required String email, required String password}) async {
    if (loginShouldFail) {
      throw Exception('Invalid credentials');
    }
    return AuthTokenResult(
      user: mockUser!,
      accessToken: 'access_123',
      refreshToken: 'refresh_123',
    );
  }

  @override
  Future<UserModel> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) async {
    return mockUser!;
  }

  @override
  Future<void> logout() async {
    logoutCalled = true;
  }
}

void main() {
  late MockAuthRepository mockRepo;
  late AuthNotifier notifier;

  final consumerUser = UserModel(
    id: 'user_1',
    email: 'consumer@example.com',
    firstName: 'Consumer',
    lastName: 'User',
    roleId: 'role_1',
    role: const RoleModel(id: 'role_1', name: 'CONSUMER'),
    userType: 'consumer',
    isActive: true,
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  final staffUser = UserModel(
    id: 'user_2',
    email: 'staff@example.com',
    firstName: 'Staff',
    lastName: 'User',
    roleId: 'role_2',
    role: const RoleModel(id: 'role_2', name: 'STAFF'),
    userType: 'business',
    isActive: true,
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  setUp(() {
    mockRepo = MockAuthRepository();
    notifier = AuthNotifier(authRepository: mockRepo);
  });

  group('AuthNotifier Tests', () {
    test('initial state is AuthInitial', () {
      expect(notifier.state, equals(AuthInitial()));
    });

    test('checkAuthStatus emits Unauthenticated when no token exists', () async {
      mockRepo.hasTokenResult = false;
      await notifier.checkAuthStatus();
      expect(notifier.state, equals(const Unauthenticated()));
    });

    test('checkAuthStatus emits Authenticated for valid Consumer account', () async {
      mockRepo.hasTokenResult = true;
      mockRepo.mockUser = consumerUser;
      await notifier.checkAuthStatus();
      expect(notifier.state, equals(Authenticated(consumerUser)));
    });

    test('checkAuthStatus rejects non-Consumer roles (e.g. STAFF)', () async {
      mockRepo.hasTokenResult = true;
      mockRepo.mockUser = staffUser;
      await notifier.checkAuthStatus();
      expect(notifier.state, isA<AuthRoleRejected>());
      expect(mockRepo.logoutCalled, isTrue);
    });

    test('login succeeds and emits Authenticated for Consumer role', () async {
      mockRepo.mockUser = consumerUser;
      final success = await notifier.login('consumer@example.com', 'password123');
      expect(success, isTrue);
      expect(notifier.state, equals(Authenticated(consumerUser)));
    });

    test('login rejects non-Consumer role (e.g. STAFF)', () async {
      mockRepo.mockUser = staffUser;
      final success = await notifier.login('staff@example.com', 'password123');
      expect(success, isFalse);
      expect(notifier.state, isA<AuthRoleRejected>());
      expect(mockRepo.logoutCalled, isTrue);
    });

    test('logout clears state and tokens', () async {
      await notifier.logout();
      expect(notifier.state, equals(const Unauthenticated()));
      expect(mockRepo.logoutCalled, isTrue);
    });
  });
}
