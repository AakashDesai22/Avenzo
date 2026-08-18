import 'dart:async';
import 'package:dio/dio.dart';
import '../constants/app_constants.dart';
import '../storage/secure_storage_service.dart';

/// Interceptor that handles attaching JWT Bearer tokens and coordinating
/// automatic token refresh on HTTP 401 Unauthorized responses.
/// Prevents concurrent request storms by queuing requests during token refresh.
class AuthInterceptor extends Interceptor {
  final SecureStorageService _storage;
  final Dio _refreshDio;
  final void Function()? onSessionExpired;

  bool _isRefreshing = false;
  final List<_PendingRequest> _queue = [];

  AuthInterceptor({
    required SecureStorageService storage,
    Dio? refreshDio,
    this.onSessionExpired,
  })  : _storage = storage,
        _refreshDio = refreshDio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiUrl,
                connectTimeout: const Duration(seconds: AppConstants.apiTimeoutSeconds),
                receiveTimeout: const Duration(seconds: AppConstants.apiTimeoutSeconds),
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                },
              ),
            );

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Attach authorization header if available
    final token = await _storage.getAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    return handler.next(options);
  }

  @override
  void onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // Check if error is 401 Unauthorized and not already on the refresh endpoint
    if (err.response?.statusCode == 401 &&
        !err.requestOptions.path.contains('/auth/refresh') &&
        !err.requestOptions.path.contains('/auth/login')) {
      
      if (_isRefreshing) {
        // Queue the request until token refresh completes
        final completer = Completer<Response>();
        _queue.add(_PendingRequest(err.requestOptions, completer, handler));
        return;
      }

      _isRefreshing = true;

      try {
        final refreshToken = await _storage.getRefreshToken();
        if (refreshToken == null || refreshToken.isEmpty) {
          throw Exception('No refresh token available');
        }

        // Perform token refresh
        final refreshResponse = await _refreshDio.post(
          '/auth/refresh',
          data: {'refresh_token': refreshToken},
        );

        if (refreshResponse.statusCode == 200 && refreshResponse.data != null) {
          final data = refreshResponse.data['data'] ?? refreshResponse.data;
          final newAccessToken = data['access_token'] as String;

          // Save new access token (keep existing refresh token)
          await _storage.saveTokens(
            accessToken: newAccessToken,
            refreshToken: refreshToken,
          );

          // Retry the failed original request
          final options = err.requestOptions;
          options.headers['Authorization'] = 'Bearer $newAccessToken';

          final retryResponse = await _refreshDio.fetch(options);

          // Process queued requests
          _processQueue(newAccessToken);

          _isRefreshing = false;
          return handler.resolve(retryResponse);
        } else {
          throw Exception('Refresh token endpoint returned non-200');
        }
      } catch (e) {
        _isRefreshing = false;
        await _storage.clearTokens();
        onSessionExpired?.call();
        _rejectQueue(err);
        return handler.next(err);
      }
    }

    return handler.next(err);
  }

  void _processQueue(String newAccessToken) async {
    for (final request in _queue) {
      request.options.headers['Authorization'] = 'Bearer $newAccessToken';
      try {
        final response = await _refreshDio.fetch(request.options);
        request.handler.resolve(response);
      } catch (e) {
        if (e is DioException) {
          request.handler.reject(e);
        } else {
          request.handler.reject(
            DioException(
              requestOptions: request.options,
              error: e,
            ),
          );
        }
      }
    }
    _queue.clear();
  }

  void _rejectQueue(DioException err) {
    for (final request in _queue) {
      request.handler.reject(err);
    }
    _queue.clear();
  }
}

class _PendingRequest {
  final RequestOptions options;
  final Completer<Response> completer;
  final ErrorInterceptorHandler handler;

  _PendingRequest(this.options, this.completer, this.handler);
}
