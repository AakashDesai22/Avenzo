import 'package:dio/dio.dart';

/// Standardized API exception model for network and server errors.
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final String? errorCode;
  final dynamic details;

  ApiException({
    required this.message,
    this.statusCode,
    this.errorCode,
    this.details,
  });

  factory ApiException.fromDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiException(
          message: 'Connection timed out. Please check your network connection.',
          statusCode: 408,
        );

      case DioExceptionType.connectionError:
        return ApiException(
          message: 'Unable to connect to the server. Please check your internet or API settings.',
          statusCode: 503,
        );

      case DioExceptionType.badResponse:
        final response = error.response;
        if (response != null && response.data is Map<String, dynamic>) {
          final data = response.data as Map<String, dynamic>;
          final message = data['message'] as String? ??
              data['detail'] as String? ??
              'An error occurred (${response.statusCode}).';
          final errorCode = data['error'] as String?;

          return ApiException(
            message: message,
            statusCode: response.statusCode,
            errorCode: errorCode,
            details: data,
          );
        }
        return ApiException(
          message: 'Server returned error status code: ${response?.statusCode}',
          statusCode: response?.statusCode,
        );

      case DioExceptionType.cancel:
        return ApiException(
          message: 'Request was cancelled.',
        );

      default:
        return ApiException(
          message: error.message ?? 'An unexpected network error occurred.',
        );
    }
  }

  @override
  String toString() => 'ApiException(statusCode: $statusCode, message: $message)';
}
