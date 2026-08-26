import 'package:equatable/equatable.dart';
import '../../marketplace/domain/marketplace_product_model.dart';

/// Consumer Cart Line Item matching backend `CartItemRead`.
class CartItemModel extends Equatable {
  final String id;
  final String cartId;
  final String productId;
  final int quantity;
  final MarketplaceProductModel? product;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const CartItemModel({
    required this.id,
    required this.cartId,
    required this.productId,
    required this.quantity,
    this.product,
    this.createdAt,
    this.updatedAt,
  });

  factory CartItemModel.fromJson(Map<String, dynamic> json) {
    MarketplaceProductModel? product;
    if (json['product'] != null && json['product'] is Map) {
      product = MarketplaceProductModel.fromJson(json['product'] as Map<String, dynamic>);
    }

    return CartItemModel(
      id: json['id'] as String,
      cartId: json['cart_id'] as String? ?? '',
      productId: json['product_id'] as String,
      quantity: json['quantity'] as int? ?? 1,
      product: product,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  double get itemTotal {
    if (product == null) return 0.0;
    return product!.unitPrice * quantity;
  }

  @override
  List<Object?> get props => [id, cartId, productId, quantity, product, createdAt, updatedAt];
}

/// Consumer Shopping Cart matching backend `CartRead`.
class CartModel extends Equatable {
  final String id;
  final String userId;
  final String status;
  final List<CartItemModel> items;
  final int totalItemsCount;
  final double calculatedSubtotal;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const CartModel({
    required this.id,
    required this.userId,
    required this.status,
    this.items = const [],
    this.totalItemsCount = 0,
    this.calculatedSubtotal = 0.0,
    this.createdAt,
    this.updatedAt,
  });

  factory CartModel.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    final items = rawItems
        .map((item) => CartItemModel.fromJson(item as Map<String, dynamic>))
        .toList();

    final rawSubtotal = json['calculated_subtotal'];
    final parsedSubtotal = rawSubtotal is num
        ? rawSubtotal.toDouble()
        : double.tryParse(rawSubtotal?.toString() ?? '0.0') ?? 0.0;

    return CartModel(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      status: json['status'] as String? ?? 'ACTIVE',
      items: items,
      totalItemsCount: json['total_items_count'] as int? ?? items.length,
      calculatedSubtotal: parsedSubtotal,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  /// Checks if any cart item is unavailable or exceeds available stock
  bool get hasUnavailableItems {
    return items.any((item) {
      if (item.product == null) return true;
      return !item.product!.isAvailable || item.quantity > item.product!.availableQuantity;
    });
  }

  @override
  List<Object?> get props => [id, userId, status, items, totalItemsCount, calculatedSubtotal, createdAt, updatedAt];
}
