import 'package:equatable/equatable.dart';

/// Individual extracted item line from a grocery receipt
class ReceiptOcrItem extends Equatable {
  final String id;
  final String rawName;
  final String normalizedName;
  final double quantity;
  final String unit;
  final double? unitPrice;
  final double? totalPrice;
  final double ocrConfidence;
  final String? matchedProductId;
  final String? matchedProductName;
  final String matchStatus; // MATCHED, SUGGESTED, UNMATCHED
  final bool isSelected;

  const ReceiptOcrItem({
    required this.id,
    required this.rawName,
    required this.normalizedName,
    required this.quantity,
    this.unit = 'units',
    this.unitPrice,
    this.totalPrice,
    this.ocrConfidence = 0.9,
    this.matchedProductId,
    this.matchedProductName,
    this.matchStatus = 'UNMATCHED',
    this.isSelected = true,
  });

  ReceiptOcrItem copyWith({
    String? id,
    String? rawName,
    String? normalizedName,
    double? quantity,
    String? unit,
    double? unitPrice,
    double? totalPrice,
    double? ocrConfidence,
    String? matchedProductId,
    String? matchedProductName,
    String? matchStatus,
    bool? isSelected,
  }) {
    return ReceiptOcrItem(
      id: id ?? this.id,
      rawName: rawName ?? this.rawName,
      normalizedName: normalizedName ?? this.normalizedName,
      quantity: quantity ?? this.quantity,
      unit: unit ?? this.unit,
      unitPrice: unitPrice ?? this.unitPrice,
      totalPrice: totalPrice ?? this.totalPrice,
      ocrConfidence: ocrConfidence ?? this.ocrConfidence,
      matchedProductId: matchedProductId ?? this.matchedProductId,
      matchedProductName: matchedProductName ?? this.matchedProductName,
      matchStatus: matchStatus ?? this.matchStatus,
      isSelected: isSelected ?? this.isSelected,
    );
  }

  @override
  List<Object?> get props => [
        id,
        rawName,
        normalizedName,
        quantity,
        unit,
        unitPrice,
        totalPrice,
        ocrConfidence,
        matchedProductId,
        matchedProductName,
        matchStatus,
        isSelected,
      ];
}

/// Complete OCR extraction result from a receipt image
class ReceiptOcrResult extends Equatable {
  final String? merchantName;
  final DateTime? receiptDate;
  final double? totalAmount;
  final String rawText;
  final List<ReceiptOcrItem> items;

  const ReceiptOcrResult({
    this.merchantName,
    this.receiptDate,
    this.totalAmount,
    required this.rawText,
    required this.items,
  });

  ReceiptOcrResult copyWith({
    String? merchantName,
    DateTime? receiptDate,
    double? totalAmount,
    String? rawText,
    List<ReceiptOcrItem>? items,
  }) {
    return ReceiptOcrResult(
      merchantName: merchantName ?? this.merchantName,
      receiptDate: receiptDate ?? this.receiptDate,
      totalAmount: totalAmount ?? this.totalAmount,
      rawText: rawText ?? this.rawText,
      items: items ?? this.items,
    );
  }

  @override
  List<Object?> get props => [merchantName, receiptDate, totalAmount, rawText, items];
}
