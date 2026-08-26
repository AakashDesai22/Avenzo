import 'package:equatable/equatable.dart';

/// Consumer-facing Product model matching backend `MarketplaceProductRead`.
/// Strictly excludes internal business fields (cost_price, supplier_id, warehouse_id, etc.).
class MarketplaceProductModel extends Equatable {
  final String id;
  final String name;
  final String? description;
  final String sku;
  final String? barcode;
  final String categoryId;
  final String? categoryName;
  final String? brandId;
  final String? brandName;
  final String unitOfMeasure;
  final double unitPrice;
  final int? shelfLifeDays;
  final bool hasExpiry;
  final String? imageUrl;
  final bool isActive;
  final int availableQuantity;
  final bool isAvailable;

  const MarketplaceProductModel({
    required this.id,
    required this.name,
    this.description,
    required this.sku,
    this.barcode,
    required this.categoryId,
    this.categoryName,
    this.brandId,
    this.brandName,
    required this.unitOfMeasure,
    required this.unitPrice,
    this.shelfLifeDays,
    required this.hasExpiry,
    this.imageUrl,
    required this.isActive,
    required this.availableQuantity,
    required this.isAvailable,
  });

  factory MarketplaceProductModel.fromJson(Map<String, dynamic> json) {
    String? categoryName;
    if (json['category'] != null && json['category'] is Map) {
      categoryName = json['category']['name'] as String?;
    }

    String? brandName;
    if (json['brand'] != null && json['brand'] is Map) {
      brandName = json['brand']['name'] as String?;
    }

    final rawPrice = json['unit_price'];
    final parsedPrice = rawPrice is num
        ? rawPrice.toDouble()
        : double.tryParse(rawPrice?.toString() ?? '0.0') ?? 0.0;

    return MarketplaceProductModel(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      sku: json['sku'] as String? ?? '',
      barcode: json['barcode'] as String?,
      categoryId: json['category_id'] as String,
      categoryName: categoryName,
      brandId: json['brand_id'] as String?,
      brandName: brandName,
      unitOfMeasure: json['unit_of_measure'] as String? ?? 'units',
      unitPrice: parsedPrice,
      shelfLifeDays: json['shelf_life_days'] as int?,
      hasExpiry: json['has_expiry'] as bool? ?? false,
      imageUrl: json['image_url'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      availableQuantity: json['available_quantity'] as int? ?? 0,
      isAvailable: json['is_available'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'sku': sku,
      'barcode': barcode,
      'category_id': categoryId,
      'unit_of_measure': unitOfMeasure,
      'unit_price': unitPrice,
      'shelf_life_days': shelfLifeDays,
      'has_expiry': hasExpiry,
      'image_url': imageUrl,
      'is_active': isActive,
      'available_quantity': availableQuantity,
      'is_available': isAvailable,
    };
  }

  @override
  List<Object?> get props => [
        id,
        name,
        description,
        sku,
        barcode,
        categoryId,
        categoryName,
        brandId,
        brandName,
        unitOfMeasure,
        unitPrice,
        shelfLifeDays,
        hasExpiry,
        imageUrl,
        isActive,
        availableQuantity,
        isAvailable,
      ];
}
