import '../../scanner/data/product_lookup_repository.dart';
import 'ocr_models.dart';

/// Service matching extracted receipt items against Avenzo Product Master catalog
class ReceiptProductMatcher {
  ReceiptProductMatcher._();

  /// Calculates string word similarity ratio (0.0 to 1.0)
  static double _calculateSimilarity(String s1, String s2) {
    final clean1 = s1.toLowerCase().trim();
    final clean2 = s2.toLowerCase().trim();

    if (clean1 == clean2) return 1.0;
    if (clean1.contains(clean2) || clean2.contains(clean1)) return 0.85;

    final words1 = clean1.split(' ').where((w) => w.length > 2).toSet();
    final words2 = clean2.split(' ').where((w) => w.length > 2).toSet();

    if (words1.isEmpty || words2.isEmpty) return 0.0;

    final intersection = words1.intersection(words2);
    return intersection.length / (words1.length > words2.length ? words1.length : words2.length);
  }

  /// Matches parsed OCR items against Product Master catalog
  static List<ReceiptOcrItem> matchItems(
    List<ReceiptOcrItem> items,
    List<ProductMasterModel> catalog,
  ) {
    if (catalog.isEmpty) return items;

    return items.map((item) {
      ProductMasterModel? bestMatch;
      double highestScore = 0.0;

      for (final prod in catalog) {
        final score = _calculateSimilarity(item.normalizedName, prod.name);
        if (score > highestScore) {
          highestScore = score;
          bestMatch = prod;
        }
      }

      if (bestMatch != null && highestScore >= 0.8) {
        return item.copyWith(
          matchedProductId: bestMatch.id,
          matchedProductName: bestMatch.name,
          unit: bestMatch.unitOfMeasure,
          matchStatus: 'MATCHED',
        );
      } else if (bestMatch != null && highestScore >= 0.4) {
        return item.copyWith(
          matchedProductId: bestMatch.id,
          matchedProductName: bestMatch.name,
          unit: bestMatch.unitOfMeasure,
          matchStatus: 'SUGGESTED',
        );
      } else {
        return item.copyWith(matchStatus: 'UNMATCHED');
      }
    }).toList();
  }
}
