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
          String message = 'An error occurred (${response.statusCode}).';
          if (data['message'] is String && (data['message'] as String).isNotEmpty) {
            message = data['message'] as String;
          } else if (data['detail'] is String) {
            message = data['detail'] as String;
          } else if (data['detail'] is List) {
            final detailsList = data['detail'] as List;
            final msgs = detailsList.map((item) {
              if (item is Map && item['msg'] != null) {
                final loc = item['loc'];
                final field = (loc is List) ? loc.where((l) => l != 'body').join('.') : '';
                return field.isNotEmpty ? '$field: ${item['msg']}' : item['msg'].toString();
              }
              return item.toString();
            }).join('; ');
            if (msgs.isNotEmpty) message = msgs;
          }

          final errorCode = data['error'] is String ? data['error'] as String : null;

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
