import 'package:flutter_test/flutter_test.dart';
import 'package:avenzo_consumer/core/constants/app_constants.dart';

void main() {
  group('AppConstants API Configuration Tests', () {
    test('productionApiBaseUrl points to verified teammavericks domain', () {
      expect(
        AppConstants.productionApiBaseUrl,
        equals('https://avenzo-cloud.teammavericks.org'),
      );
    });

    test('apiBaseUrl defaults to production domain without trailing slash', () {
      expect(
        AppConstants.apiBaseUrl,
        equals('https://avenzo-cloud.teammavericks.org'),
      );
      expect(AppConstants.apiBaseUrl.endsWith('/'), isFalse);
    });

    test('apiVersion is /api/v1', () {
      expect(AppConstants.apiVersion, equals('/api/v1'));
    });

    test('apiUrl constructs correct full URL without double slashes', () {
      expect(
        AppConstants.apiUrl,
        equals('https://avenzo-cloud.teammavericks.org/api/v1'),
      );
      expect(AppConstants.apiUrl.contains('//api'), isFalse);
    });

    test('endpoint paths compose cleanly with apiUrl', () {
      final pantryEndpoint = '${AppConstants.apiUrl}/pantry';
      expect(
        pantryEndpoint,
        equals('https://avenzo-cloud.teammavericks.org/api/v1/pantry'),
      );
    });
  });
}
