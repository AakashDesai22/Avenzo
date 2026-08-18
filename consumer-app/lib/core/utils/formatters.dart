import 'package:intl/intl.dart';

/// Formatting utilities for dates, currency, and DTE (Days to Expiry).
class Formatters {
  Formatters._();

  static final _currencyFormat = NumberFormat.currency(
    symbol: '₹',
    locale: 'en_IN',
    decimalDigits: 2,
  );

  /// Format numeric price into INR standard (₹1,250.00)
  static String currency(dynamic amount) {
    if (amount == null) return '₹0.00';
    final numValue = amount is String ? double.tryParse(amount) ?? 0.0 : amount as num;
    return _currencyFormat.format(numValue);
  }

  /// Format date to readable string (e.g., "18 Aug 2026")
  static String formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return DateFormat('d MMM yyyy').format(date);
  }

  /// Format DTE (Days to Expiry) badge label
  static String formatDTE(DateTime? expiryDate) {
    if (expiryDate == null) return 'No Expiry';
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final expiry = DateTime(expiryDate.year, expiryDate.month, expiryDate.day);
    final days = expiry.difference(today).inDays;

    if (days < 0) {
      return 'Expired ${days.abs()}d ago';
    } else if (days == 0) {
      return 'Expires Today';
    } else if (days == 1) {
      return 'Expires Tomorrow';
    } else {
      return '$days days left';
    }
  }
}
