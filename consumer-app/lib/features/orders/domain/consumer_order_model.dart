import 'package:equatable/equatable.dart';
import '../../marketplace/domain/marketplace_product_model.dart';

/// Consumer Order Line Item matching backend `OrderItemRead`.
class ConsumerOrderItemModel extends Equatable {
  final String id;
  final String orderId;
  final String productId;
  final int quantity;
  final double unitPrice;
  final double totalPrice;
  final String fulfillmentStatus;
  final MarketplaceProductModel? product;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const ConsumerOrderItemModel({
    required this.id,
    required this.orderId,
    required this.productId,
    required this.quantity,
    required this.unitPrice,
    required this.totalPrice,
    required this.fulfillmentStatus,
    this.product,
    this.createdAt,
    this.updatedAt,
  });

  factory ConsumerOrderItemModel.fromJson(Map<String, dynamic> json) {
    MarketplaceProductModel? product;
    if (json['product'] != null && json['product'] is Map) {
      product = MarketplaceProductModel.fromJson(json['product'] as Map<String, dynamic>);
    }

    final rawUnitPrice = json['unit_price'];
    final parsedUnitPrice = rawUnitPrice is num
        ? rawUnitPrice.toDouble()
        : double.tryParse(rawUnitPrice?.toString() ?? '0.0') ?? 0.0;

    final rawTotalPrice = json['total_price'];
    final parsedTotalPrice = rawTotalPrice is num
        ? rawTotalPrice.toDouble()
        : double.tryParse(rawTotalPrice?.toString() ?? '0.0') ?? 0.0;

    return ConsumerOrderItemModel(
      id: json['id'] as String,
      orderId: json['order_id'] as String? ?? '',
      productId: json['product_id'] as String,
      quantity: json['quantity'] as int? ?? 1,
      unitPrice: parsedUnitPrice,
      totalPrice: parsedTotalPrice,
      fulfillmentStatus: json['fulfillment_status'] as String? ?? 'UNALLOCATED',
      product: product,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  @override
  List<Object?> get props => [
        id,
        orderId,
        productId,
        quantity,
        unitPrice,
        totalPrice,
        fulfillmentStatus,
        product,
        createdAt,
        updatedAt,
      ];
}

/// Consumer Purchase Order matching backend `OrderRead`.
class ConsumerOrderModel extends Equatable {
  final String id;
  final String orderNumber;
  final String userId;
  final String status;
  final String paymentStatus;
  final String paymentMethod;
  final double subtotal;
  final double deliveryFee;
  final double totalAmount;
  final String shippingAddress;
  final String? notes;
  final List<ConsumerOrderItemModel> items;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const ConsumerOrderModel({
    required this.id,
    required this.orderNumber,
    required this.userId,
    required this.status,
    required this.paymentStatus,
    required this.paymentMethod,
    required this.subtotal,
    required this.deliveryFee,
    required this.totalAmount,
    required this.shippingAddress,
    this.notes,
    this.items = const [],
    this.createdAt,
    this.updatedAt,
  });

  factory ConsumerOrderModel.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    final items = rawItems
        .map((item) => ConsumerOrderItemModel.fromJson(item as Map<String, dynamic>))
        .toList();

    double parseDouble(dynamic val) {
      if (val is num) return val.toDouble();
      return double.tryParse(val?.toString() ?? '0.0') ?? 0.0;
    }

    return ConsumerOrderModel(
      id: json['id'] as String,
      orderNumber: json['order_number'] as String? ?? '',
      userId: json['user_id'] as String,
      status: json['status'] as String? ?? 'PENDING',
      paymentStatus: json['payment_status'] as String? ?? 'UNPAID',
      paymentMethod: json['payment_method'] as String? ?? 'MOCK_PAYMENT',
      subtotal: parseDouble(json['subtotal']),
      deliveryFee: parseDouble(json['delivery_fee']),
      totalAmount: parseDouble(json['total_amount']),
      shippingAddress: json['shipping_address'] as String? ?? '',
      notes: json['notes'] as String?,
      items: items,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at'].toString()) : null,
    );
  }

  /// Check if consumer can cancel pre-shipment order
  bool get canCancel {
    return ['PENDING', 'CONFIRMED', 'ALLOCATED', 'PACKED'].contains(status);
  }

  @override
  List<Object?> get props => [
        id,
        orderNumber,
        userId,
        status,
        paymentStatus,
        paymentMethod,
        subtotal,
        deliveryFee,
        totalAmount,
        shippingAddress,
        notes,
        items,
        createdAt,
        updatedAt,
      ];
}
