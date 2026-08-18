// AVENZO Consumer App — App Constants
// All API URLs, config values, and app-wide constants.
// NO hardcoded URLs allowed in feature code — use this file.

class AppConstants {
  AppConstants._(); // Prevent instantiation

  // ==========================================================================
  // API Configuration
  // ==========================================================================

  /// Base URL for the AVENZO backend API.
  /// Override this via dart-define or flavor configuration.
  static const String apiBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');

  /// API version prefix
  static const String apiVersion = '/api/v1';

  /// Full API base URL with version
  static const String apiUrl = '$apiBaseUrl$apiVersion';

  // ==========================================================================
  // App Metadata
  // ==========================================================================

  static const String appName = 'AVENZO';
  static const String appTagline = 'One Product. One Lifecycle. One Intelligence.';
  static const String appVersion = '0.1.0';

  // ==========================================================================
  // Shared Preferences Keys
  // ==========================================================================

  static const String keyAccessToken = 'access_token';
  static const String keyRefreshToken = 'refresh_token';
  static const String keyUserId = 'user_id';
  static const String keyUserRole = 'user_role';
  static const String keyUserEmail = 'user_email';

  // ==========================================================================
  // Pagination
  // ==========================================================================

  static const int defaultPageSize = 20;
  static const int maxPageSize = 100;

  // ==========================================================================
  // Expiry Warning Thresholds (days)
  // ==========================================================================

  static const int expiryWarningDays = 7;   // Warn 7 days before expiry
  static const int expiryCriticalDays = 3;  // Critical alert 3 days before

  // ==========================================================================
  // Timeouts
  // ==========================================================================

  static const int apiTimeoutSeconds = 30;
  static const int uploadTimeoutSeconds = 120;
}
