import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/models/pantry_item_model.dart';

/// Repository managing Digital Pantry API interactions using centralized ApiClient.
class PantryRepository {
  final ApiClient _apiClient;

  PantryRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  /// List consumer's active pantry items with optional location filtering
  Future<List<PantryItemModel>> getPantryItems({
    String? storageLocation,
    String status = 'active',
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'status': status,
      };
      if (storageLocation != null && storageLocation.isNotEmpty) {
        queryParams['storage_location'] = storageLocation;
      }

      final response = await _apiClient.get(
        '/pantry',
        queryParameters: queryParams,
      );

      final body = response.data as Map<String, dynamic>;
      final listData = body['data'] as List<dynamic>;

      return listData
          .map((item) => PantryItemModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to fetch pantry items: ${e.toString()}');
    }
  }

  /// Get single pantry item detail by ID
  Future<PantryItemModel> getPantryItem(String id) async {
    try {
      final response = await _apiClient.get('/pantry/$id');
      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return PantryItemModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to fetch pantry item details: ${e.toString()}');
    }
  }

  /// Add custom or product item to pantry
  Future<PantryItemModel> addPantryItem({
    String? productId,
    String? batchId,
    String? customName,
    String? barcode,
    required double quantity,
    required String unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    required String storageLocation,
    String? notes,
  }) async {
    try {
      final payload = <String, dynamic>{
        if (productId != null) 'product_id': productId,
        if (batchId != null) 'batch_id': batchId,
        if (customName != null && customName.isNotEmpty) 'custom_name': customName,
        if (barcode != null && barcode.isNotEmpty) 'barcode': barcode,
        'quantity': quantity,
        'unit': unit,
        if (purchaseDate != null)
          'purchase_date': purchaseDate.toIso8601String().split('T').first,
        if (expiryDate != null)
          'expiry_date': expiryDate.toIso8601String().split('T').first,
        'storage_location': storageLocation,
        if (notes != null && notes.isNotEmpty) 'notes': notes,
      };

      final response = await _apiClient.post(
        '/pantry',
        data: payload,
      );

      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return PantryItemModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to add item to pantry: ${e.toString()}');
    }
  }

  /// Update pantry item details or quantity
  Future<PantryItemModel> updatePantryItem({
    required String id,
    String? customName,
    double? quantity,
    String? unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    String? storageLocation,
    String? notes,
  }) async {
    try {
      final payload = <String, dynamic>{
        if (customName != null) 'custom_name': customName,
        if (quantity != null) 'quantity': quantity,
        if (unit != null) 'unit': unit,
        if (purchaseDate != null)
          'purchase_date': purchaseDate.toIso8601String().split('T').first,
        if (expiryDate != null)
          'expiry_date': expiryDate.toIso8601String().split('T').first,
        if (storageLocation != null) 'storage_location': storageLocation,
        if (notes != null) 'notes': notes,
      };

      final response = await _apiClient.put(
        '/pantry/$id',
        data: payload,
      );

      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return PantryItemModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to update pantry item: ${e.toString()}');
    }
  }

  /// Soft delete pantry item
  Future<PantryItemModel> deletePantryItem(String id) async {
    try {
      final response = await _apiClient.delete('/pantry/$id');
      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return PantryItemModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to delete pantry item: ${e.toString()}');
    }
  }

  /// Consume specified quantity from pantry item
  Future<PantryItemModel> consumeItem(String id, double quantity) async {
    try {
      final response = await _apiClient.post(
        '/pantry/$id/consume',
        data: {'quantity': quantity},
      );

      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return PantryItemModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to consume item: ${e.toString()}');
    }
  }

  /// Discard/waste specified quantity from pantry item
  Future<PantryItemModel> discardItem(String id, double quantity) async {
    try {
      final response = await _apiClient.post(
        '/pantry/$id/discard',
        data: {'quantity': quantity},
      );

      final body = response.data as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return PantryItemModel.fromJson(data);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to discard item: ${e.toString()}');
    }
  }

  /// Get active items sorted by DTE ASC
  Future<List<PantryItemModel>> getExpiringItems() async {
    try {
      final response = await _apiClient.get('/pantry/expiring');
      final body = response.data as Map<String, dynamic>;
      final listData = body['data'] as List<dynamic>;

      return listData
          .map((item) => PantryItemModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(message: 'Failed to fetch expiring items: ${e.toString()}');
    }
  }
}
