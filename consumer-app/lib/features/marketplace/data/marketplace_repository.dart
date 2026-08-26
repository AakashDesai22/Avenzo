import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../domain/marketplace_product_model.dart';

final marketplaceRepositoryProvider = Provider<MarketplaceRepository>((ref) {
  return MarketplaceRepository(apiClient: ApiClient());
});

/// Repository interfacing with backend Consumer Marketplace endpoints (`/api/v1/marketplace`).
class MarketplaceRepository {
  final ApiClient _apiClient;

  MarketplaceRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Fetches consumer marketplace catalog products with filters and pagination.
  Future<List<MarketplaceProductModel>> getProducts({
    int page = 1,
    int perPage = 20,
    String? categoryId,
    String? search,
    bool inStockOnly = false,
  }) async {
    final queryParams = <String, dynamic>{
      'page': page,
      'per_page': perPage,
      'in_stock_only': inStockOnly,
    };

    if (categoryId != null && categoryId.isNotEmpty) {
      queryParams['category_id'] = categoryId;
    }
    if (search != null && search.trim().isNotEmpty) {
      queryParams['search'] = search.trim();
    }

    final response = await _apiClient.get(
      '/marketplace/products',
      queryParameters: queryParams,
    );

    if (response.statusCode == 200 && response.data != null) {
      final body = response.data as Map<String, dynamic>;
      final rawList = body['data'] as List<dynamic>? ?? [];
      return rawList
          .map((item) => MarketplaceProductModel.fromJson(item as Map<String, dynamic>))
          .toList();
    }

    return [];
  }

  /// Fetches detailed marketplace product view by ID.
  Future<MarketplaceProductModel?> getProductById(String productId) async {
    final response = await _apiClient.get('/marketplace/products/$productId');
    if (response.statusCode == 200 && response.data != null) {
      final body = response.data as Map<String, dynamic>;
      final rawData = body['data'] as Map<String, dynamic>?;
      if (rawData != null) {
        return MarketplaceProductModel.fromJson(rawData);
      }
    }
    return null;
  }
}
