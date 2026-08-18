/// Generic API Response envelope matching backend `ApiResponse[T]`.
class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? message;
  final String? error;
  final dynamic meta;

  const ApiResponse({
    required this.success,
    this.data,
    this.message,
    this.error,
    this.meta,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic json) fromJsonT,
  ) {
    return ApiResponse<T>(
      success: json['success'] as bool? ?? false,
      data: json['data'] != null ? fromJsonT(json['data']) : null,
      message: json['message'] as String?,
      error: json['error'] as String?,
      meta: json['meta'],
    );
  }
}
