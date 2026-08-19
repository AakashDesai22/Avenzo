import 'ocr_models.dart';

/// Rule-based parser that converts raw OCR text into structured ReceiptOcrResult items.
class ReceiptLineParser {
  ReceiptLineParser._();

  static final List<String> _noiseKeywords = [
    'TOTAL',
    'SUBTOTAL',
    'SUB TOTAL',
    'TAX',
    'VAT',
    'GST',
    'CGST',
    'SGST',
    'IGST',
    'CASH',
    'CARD',
    'DEBIT',
    'CREDIT',
    'UPI',
    'PAYMENT',
    'CHANGE',
    'BALANCE',
    'DISCOUNT',
    'SAVINGS',
    'THANK YOU',
    'THANKYOU',
    'WELCOME',
    'TEL:',
    'PHONE',
    'DATE',
    'TIME',
    'INV NO',
    'BILL NO',
    'RECEIPT',
    'ADDRESS',
    'ITEMS SOLD',
  ];

  /// Tests whether a line is a non-product noise line
  static bool isNoiseLine(String line) {
    final upper = line.trim().toUpperCase();
    if (upper.isEmpty) return true;
    for (final kw in _noiseKeywords) {
      if (upper.contains(kw)) return true;
    }
    return false;
  }

  /// Normalizes product line description
  static String normalizeProductName(String rawName) {
    var cleaned = rawName.replaceAll(RegExp(r'[\$\₹]?\s*\d+\.\d{2}'), '');
    cleaned = cleaned.replaceAll(RegExp(r'^\d+\s*x\s*|^\d+\s*'), '');
    cleaned = cleaned.replaceAll(RegExp(r'\s+'), ' ').trim();
    return cleaned;
  }

  /// Parses raw OCR text output into a structured ReceiptOcrResult
  static ReceiptOcrResult parseText(String rawText) {
    final lines = rawText.split('\n').map((l) => l.trim()).where((l) => l.isNotEmpty).toList();
    if (lines.isEmpty) {
      return const ReceiptOcrResult(rawText: '', items: []);
    }

    String? merchantName;
    DateTime? receiptDate;
    double? totalAmount;
    final List<ReceiptOcrItem> items = [];

    final priceRegex = RegExp(r'[\$\₹]?\s*(\d+\.\d{2})');
    final qtyRegex = RegExp(r'^(\d+(?:\.\d+)?)\s*(?:x|X)\s+');
    final dateRegex = RegExp(r'(\d{4}[-/]\d{2}[-/]\d{2})|(\d{2}[-/]\d{2}[-/]\d{4})');

    int itemCounter = 1;

    for (int i = 0; i < lines.length; i++) {
      final line = lines[i];

      // Extract Merchant Name from first non-noise header line
      if (merchantName == null && i < 4 && !isNoiseLine(line) && !line.contains(RegExp(r'\d'))) {
        merchantName = line.trim();
        continue;
      }

      // Extract Receipt Date
      if (receiptDate == null) {
        final dateMatch = dateRegex.firstMatch(line);
        if (dateMatch != null) {
          try {
            final rawDateStr = dateMatch.group(0)!.replaceAll('/', '-');
            final parts = rawDateStr.split('-');
            if (parts[0].length == 4) {
              receiptDate = DateTime.parse(rawDateStr);
            } else if (parts[2].length == 4) {
              receiptDate = DateTime(int.parse(parts[2]), int.parse(parts[1]), int.parse(parts[0]));
            }
          } catch (_) {}
        }
      }

      // Check Total line
      if (line.toUpperCase().contains('TOTAL') && !line.toUpperCase().contains('SUBTOTAL')) {
        final priceMatch = priceRegex.firstMatch(line);
        if (priceMatch != null) {
          totalAmount = double.tryParse(priceMatch.group(1)!);
        }
        continue;
      }

      // Skip non-product noise lines
      if (isNoiseLine(line)) continue;

      // Extract Price & Quantity
      final priceMatch = priceRegex.firstMatch(line);
      double? totalPrice;
      if (priceMatch != null) {
        totalPrice = double.tryParse(priceMatch.group(1)!);
      }

      double quantity = 1.0;
      final qtyMatch = qtyRegex.firstMatch(line);
      if (qtyMatch != null) {
        quantity = double.tryParse(qtyMatch.group(1)!) ?? 1.0;
      }

      final normalized = normalizeProductName(line);
      if (normalized.length >= 2) {
        items.add(ReceiptOcrItem(
          id: 'ocr-item-$itemCounter',
          rawName: line,
          normalizedName: normalized,
          quantity: quantity,
          unit: 'units',
          totalPrice: totalPrice,
          ocrConfidence: 0.92,
          isSelected: true,
        ));
        itemCounter++;
      }
    }

    return ReceiptOcrResult(
      merchantName: merchantName ?? 'Grocery Store',
      receiptDate: receiptDate ?? DateTime.now(),
      totalAmount: totalAmount,
      rawText: rawText,
      items: items,
    );
  }
}
