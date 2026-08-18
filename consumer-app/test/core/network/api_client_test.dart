import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:avenzo_consumer/core/network/auth_interceptor.dart';
import 'package:avenzo_consumer/core/storage/secure_storage_service.dart';

class MockSecureStorageService extends SecureStorageService {
  String? mockAccessToken;
  String? mockRefreshToken;
  bool cleared = false;

  MockSecureStorageService({this.mockAccessToken, this.mockRefreshToken});

  @override
  Future<String?> getAccessToken() async => mockAccessToken;

  @override
  Future<String?> getRefreshToken() async => mockRefreshToken;

  @override
  Future<void> saveTokens({required String accessToken, required String refreshToken}) async {
    mockAccessToken = accessToken;
    mockRefreshToken = refreshToken;
  }

  @override
  Future<void> clearTokens() async {
    cleared = true;
    mockAccessToken = null;
    mockRefreshToken = null;
  }
}

void main() {
  group('AuthInterceptor Tests', () {
    test('attaches Authorization header when access token exists', () async {
      final storage = MockSecureStorageService(mockAccessToken: 'test_access_token');
      final interceptor = AuthInterceptor(storage: storage);

      final options = RequestOptions(path: '/test');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(options.headers['Authorization'], equals('Bearer test_access_token'));
    });

    test('does not attach Authorization header when token is null', () async {
      final storage = MockSecureStorageService(mockAccessToken: null);
      final interceptor = AuthInterceptor(storage: storage);

      final options = RequestOptions(path: '/test');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(options.headers.containsKey('Authorization'), isFalse);
    });
  });
}
