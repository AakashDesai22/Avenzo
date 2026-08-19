import 'package:equatable/equatable.dart';
import 'package:intl/intl.dart';

/// Product summary nested inside PantryItemModel
class ProductSummaryModel extends Equatable {
  final String id;
  final String name;
  final String sku;
  final String? barcode;
  final String? imageUrl;
  final int? shelfLifeDays;
  final bool hasExpiry;

  const ProductSummaryModel({
    required this.id,
    required this.name,
    required this.sku,
    this.barcode,
    this.imageUrl,
    this.shelfLifeDays,
    required this.hasExpiry,
  });

  factory ProductSummaryModel.fromJson(Map<String, dynamic> json) {
    return ProductSummaryModel(
      id: json['id'] as String,
      name: json['name'] as String? ?? 'Product',
      sku: json['sku'] as String? ?? '',
      barcode: json['barcode'] as String?,
      imageUrl: json['image_url'] as String?,
      shelfLifeDays: json['shelf_life_days'] as int?,
      hasExpiry: json['has_expiry'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'sku': sku,
      'barcode': barcode,
      'image_url': imageUrl,
      'shelf_life_days': shelfLifeDays,
      'has_expiry': hasExpiry,
    };
  }

  @override
  List<Object?> get props => [id, name, sku, barcode, imageUrl, shelfLifeDays, hasExpiry];
}

/// Pantry item model matching FastAPI PantryItemRead schema.
class PantryItemModel extends Equatable {
  final String id;
  final String pantryId;
  final String? productId;
  final ProductSummaryModel? product;
  final String? batchId;
  final String? customName;
  final String? barcode;
  final double quantity;
  final String unit;
  final DateTime? purchaseDate;
  final DateTime? expiryDate;
  final String storageLocation;
  final String status;
  final String? notes;
  final int? daysToExpiry;
  final String expiryStatus;
  final DateTime createdAt;
  final DateTime updatedAt;

  const PantryItemModel({
    required this.id,
    required this.pantryId,
    this.productId,
    this.product,
    this.batchId,
    this.customName,
    this.barcode,
    required this.quantity,
    required this.unit,
    this.purchaseDate,
    this.expiryDate,
    required this.storageLocation,
    required this.status,
    this.notes,
    this.daysToExpiry,
    required this.expiryStatus,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Resolved display name prioritizing product name over custom name
  String get displayName {
    if (product != null && product!.name.isNotEmpty) {
      return product!.name;
    }
    if (customName != null && customName!.isNotEmpty) {
      return customName!;
    }
    return 'Unidentified Item';
  }

  /// Formatted expiry date string e.g. "Aug 24, 2026"
  String get formattedExpiry {
    if (expiryDate == null) return 'No expiry date';
    return DateFormat.yMMMd().format(expiryDate!);
  }

  /// Human readable DTE string e.g. "5 days left", "Expired 2 days ago"
  String get formattedDte {
    if (expiryStatus == 'N/A' || daysToExpiry == null) {
      return 'No expiry';
    }
    final dte = daysToExpiry!;
    if (dte < 0) {
      final absDays = dte.abs();
      return 'Expired $absDays ${absDays == 1 ? 'day' : 'days'} ago';
    } else if (dte == 0) {
      return 'Expires today';
    } else if (dte == 1) {
      return '1 day left';
    } else {
      return '$dte days left';
    }
  }

  factory PantryItemModel.fromJson(Map<String, dynamic> json) {
    return PantryItemModel(
      id: json['id'] as String,
      pantryId: json['pantry_id'] as String? ?? '',
      productId: json['product_id'] as String?,
      product: json['product'] != null
          ? ProductSummaryModel.fromJson(json['product'] as Map<String, dynamic>)
          : null,
      batchId: json['batch_id'] as String?,
      customName: json['custom_name'] as String?,
      barcode: json['barcode'] as String?,
      quantity: (json['quantity'] is num)
          ? (json['quantity'] as num).toDouble()
          : double.tryParse(json['quantity'].toString()) ?? 1.0,
      unit: json['unit'] as String? ?? 'units',
      purchaseDate: json['purchase_date'] != null
          ? DateTime.tryParse(json['purchase_date'] as String)
          : null,
      expiryDate: json['expiry_date'] != null
          ? DateTime.tryParse(json['expiry_date'] as String)
          : null,
      storageLocation: json['storage_location'] as String? ?? 'pantry',
      status: json['status'] as String? ?? 'active',
      notes: json['notes'] as String?,
      daysToExpiry: json['days_to_expiry'] as int?,
      expiryStatus: json['expiry_status'] as String? ?? 'N/A',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'pantry_id': pantryId,
      'product_id': productId,
      'product': product?.toJson(),
      'batch_id': batchId,
      'custom_name': customName,
      'barcode': barcode,
      'quantity': quantity,
      'unit': unit,
      'purchase_date': purchaseDate?.toIso8601String().split('T').first,
      'expiry_date': expiryDate?.toIso8601String().split('T').first,
      'storage_location': storageLocation,
      'status': status,
      'notes': notes,
      'days_to_expiry': daysToExpiry,
      'expiry_status': expiryStatus,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  PantryItemModel copyWith({
    String? id,
    String? pantryId,
    String? productId,
    ProductSummaryModel? product,
    String? batchId,
    String? customName,
    String? barcode,
    double? quantity,
    String? unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    String? storageLocation,
    String? status,
    String? notes,
    int? daysToExpiry,
    String? expiryStatus,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return PantryItemModel(
      id: id ?? this.id,
      pantryId: pantryId ?? this.pantryId,
      productId: productId ?? this.productId,
      product: product ?? this.product,
      batchId: batchId ?? this.batchId,
      customName: customName ?? this.customName,
      barcode: barcode ?? this.barcode,
      quantity: quantity ?? this.quantity,
      unit: unit ?? this.unit,
      purchaseDate: purchaseDate ?? this.purchaseDate,
      expiryDate: expiryDate ?? this.expiryDate,
      storageLocation: storageLocation ?? this.storageLocation,
      status: status ?? this.status,
      notes: notes ?? this.notes,
      daysToExpiry: daysToExpiry ?? this.daysToExpiry,
      expiryStatus: expiryStatus ?? this.expiryStatus,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        pantryId,
        productId,
        product,
        batchId,
        customName,
        barcode,
        quantity,
        unit,
        purchaseDate,
        expiryDate,
        storageLocation,
        status,
        notes,
        daysToExpiry,
        expiryStatus,
        createdAt,
        updatedAt,
      ];
}
