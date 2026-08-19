import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';

/// Product Master model returned from barcode lookup
class ProductMasterModel {
  final String id;
  final String name;
  final String sku;
  final String? barcode;
  final String? brandName;
  final String? categoryName;
  final String unitOfMeasure;
  final int? shelfLifeDays;
  final String? imageUrl;

  const ProductMasterModel({
    required this.id,
    required this.name,
    required this.sku,
    this.barcode,
    this.brandName,
    this.categoryName,
    this.unitOfMeasure = 'units',
    this.shelfLifeDays,
    this.imageUrl,
  });

  factory ProductMasterModel.fromJson(Map<String, dynamic> json) {
    String? brand;
    if (json['brand'] != null && json['brand']['name'] != null) {
      brand = json['brand']['name'].toString();
    }

    String? category;
    if (json['category'] != null && json['category']['name'] != null) {
      category = json['category']['name'].toString();
    }

    return ProductMasterModel(
      id: json['id'].toString(),
      name: json['name']?.toString() ?? 'Unknown Product',
      sku: json['sku']?.toString() ?? '',
      barcode: json['barcode']?.toString(),
      brandName: brand,
      categoryName: category,
      unitOfMeasure: json['unit_of_measure']?.toString() ?? 'units',
      shelfLifeDays: json['shelf_life_days'] != null
          ? int.tryParse(json['shelf_life_days'].toString())
          : null,
      imageUrl: json['image_url']?.toString(),
    );
  }
}

/// Repository wrapper for Product Master barcode lookup
class ProductLookupRepository {
  final ApiClient _apiClient;

  ProductLookupRepository({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  /// Normalizes raw barcode input string (trims leading/trailing whitespace, preserves strings)
  static String normalizeBarcode(String rawBarcode) {
    return rawBarcode.trim();
  }

  /// Looks up product by barcode from Avenzo Product Master (`GET /api/v1/products?barcode={barcode}`)
  Future<ProductMasterModel?> lookupByBarcode(String barcode) async {
    final cleanBarcode = normalizeBarcode(barcode);
    if (cleanBarcode.isEmpty) return null;

    try {
      final response = await _apiClient.get(
        '/api/v1/products',
        queryParameters: {'barcode': cleanBarcode},
      );

      final List<dynamic> data = response.data['data'] ?? [];
      if (data.isNotEmpty) {
        return ProductMasterModel.fromJson(data.first as Map<String, dynamic>);
      }

      // Fallback search parameter if explicit barcode match was empty
      final fallbackResponse = await _apiClient.get(
        '/api/v1/products',
        queryParameters: {'search': cleanBarcode},
      );

      final List<dynamic> fallbackData = fallbackResponse.data['data'] ?? [];
      if (fallbackData.isNotEmpty) {
        return ProductMasterModel.fromJson(fallbackData.first as Map<String, dynamic>);
      }

      return null; // Product not found
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to perform product lookup: $e');
    }
  }
}
