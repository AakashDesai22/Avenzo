import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/storage/secure_storage_service.dart';
import '../../../shared/models/user_model.dart';

/// Data class holding login token response
class AuthTokenResult {
  final UserModel user;
  final String accessToken;
  final String refreshToken;

  const AuthTokenResult({
    required this.user,
    required this.accessToken,
    required this.refreshToken,
  });
}

/// Repository managing authentication API calls and token storage.
class AuthRepository {
  final ApiClient _apiClient;
  final SecureStorageService _storage;

  AuthRepository({
    ApiClient? apiClient,
    SecureStorageService? storage,
  })  : _apiClient = apiClient ?? ApiClient(),
        _storage = storage ?? SecureStorageService();

  /// Authenticate credentials against POST /api/v1/auth/login
  Future<AuthTokenResult> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/login',
        data: {
          'email': email.trim(),
          'password': password,
        },
      );

      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;

      final accessToken = data['access_token'] as String;
      final refreshToken = data['refresh_token'] as String;
      final user = UserModel.fromJson(data['user'] as Map<String, dynamic>);

      // Persist tokens securely
      await _storage.saveTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );

      return AuthTokenResult(
        user: user,
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Login failed: ${e.toString()}');
    }
  }

  /// Register consumer account against POST /api/v1/auth/register
  Future<UserModel> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/register',
        data: {
          'email': email.trim(),
          'password': password,
          'first_name': firstName.trim(),
          'last_name': lastName.trim(),
          'phone': phone?.trim().isNotEmpty == true ? phone!.trim() : null,
          'user_type': 'consumer',
        },
      );

      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return UserModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Registration failed: ${e.toString()}');
    }
  }

  /// Fetch authenticated profile from GET /api/v1/auth/me
  Future<UserModel> getCurrentUser() async {
    try {
      final response = await _apiClient.get('/auth/me');
      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return UserModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to fetch profile: ${e.toString()}');
    }
  }

  /// Clear tokens on logout
  Future<void> logout() async {
    await _storage.clearTokens();
  }

  /// Check if an access token exists in secure storage
  Future<bool> hasToken() async {
    final token = await _storage.getAccessToken();
    return token != null && token.isNotEmpty;
  }
}
