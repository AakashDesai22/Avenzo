import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/models/user_model.dart';
import '../data/auth_repository.dart';

/// Sealed state representation for AuthState
abstract class AuthState extends Equatable {
  const AuthState();

  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

class Authenticated extends AuthState {
  final UserModel user;

  const Authenticated(this.user);

  @override
  List<Object?> get props => [user];
}

class Unauthenticated extends AuthState {
  final String? errorMessage;

  const Unauthenticated([this.errorMessage]);

  @override
  List<Object?> get props => [errorMessage];
}

class AuthRoleRejected extends AuthState {
  final String message;

  const AuthRoleRejected(this.message);

  @override
  List<Object?> get props => [message];
}

/// Provider for AuthRepository
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});

/// AuthNotifier Provider managing authentication state
final authNotifierProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(authRepository: ref.watch(authRepositoryProvider));
});

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _authRepository;

  AuthNotifier({required AuthRepository authRepository})
      : _authRepository = authRepository,
        super(AuthInitial());

  /// Check stored tokens and validate role via GET /api/v1/auth/me
  Future<void> checkAuthStatus() async {
    state = AuthLoading();
    try {
      final hasToken = await _authRepository.hasToken();
      if (!hasToken) {
        state = const Unauthenticated();
        return;
      }

      // Backend is source of truth: retrieve current user profile
      final user = await _authRepository.getCurrentUser();

      // Consumer Role Validation
      if (!user.isConsumer) {
        await _authRepository.logout();
        state = const AuthRoleRejected(
          'Access Restricted: This application is exclusively for Consumer accounts. '
          'Please use the Avenzo Business Web Portal for Staff or Manager access.',
        );
        return;
      }

      state = Authenticated(user);
    } catch (e) {
      await _authRepository.logout();
      state = Unauthenticated(
        e is ApiException ? e.message : 'Session expired. Please log in again.',
      );
    }
  }

  /// Perform user login and enforce Consumer role check
  Future<bool> login(String email, String password) async {
    state = AuthLoading();
    try {
      await _authRepository.login(email: email, password: password);

      // Backend is source of truth: fetch profile to confirm user role
      final user = await _authRepository.getCurrentUser();

      if (!user.isConsumer) {
        await _authRepository.logout();
        state = const AuthRoleRejected(
          'Access Restricted: This application is exclusively for Consumer accounts. '
          'Please use the Avenzo Business Web Portal for Staff or Manager access.',
        );
        return false;
      }

      state = Authenticated(user);
      return true;
    } catch (e) {
      final message = e is ApiException ? e.message : 'Login failed. Please check credentials.';
      state = Unauthenticated(message);
      return false;
    }
  }

  /// Perform user registration
  Future<bool> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) async {
    state = AuthLoading();
    try {
      await _authRepository.register(
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
        phone: phone,
      );

      // Auto-login after registration
      return await login(email, password);
    } catch (e) {
      final message = e is ApiException ? e.message : 'Registration failed. Please try again.';
      state = Unauthenticated(message);
      return false;
    }
  }

  /// Clean logout
  Future<void> logout() async {
    state = AuthLoading();
    await _authRepository.logout();
    state = const Unauthenticated();
  }
}
