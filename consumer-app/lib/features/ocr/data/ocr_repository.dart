import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import '../../scanner/data/product_lookup_repository.dart';
import 'ocr_models.dart';
import 'receipt_line_parser.dart';
import 'receipt_product_matcher.dart';

/// Repository handling on-device ML Kit OCR recognition and item parsing
class OcrRepository {
  final TextRecognizer _textRecognizer;

  OcrRepository({TextRecognizer? textRecognizer})
      : _textRecognizer = textRecognizer ?? TextRecognizer(script: TextRecognitionScript.latin);

  /// Performs on-device OCR processing on a receipt image file
  Future<ReceiptOcrResult> processReceiptImage(
    File imageFile, {
    List<ProductMasterModel> catalog = const [],
  }) async {
    try {
      final inputImage = InputImage.fromFile(imageFile);
      final RecognizedText recognizedText = await _textRecognizer.processImage(inputImage);
      final rawText = recognizedText.text;

      // 1. Parse raw text lines into structured items
      final result = ReceiptLineParser.parseText(rawText);

      // 2. Match parsed items against Product Master catalog
      final matchedItems = ReceiptProductMatcher.matchItems(result.items, catalog);

      return result.copyWith(items: matchedItems);
    } catch (e) {
      debugPrint('OCR Recognition Error: $e');
      throw Exception('Failed to process receipt image: $e');
    }
  }

  void dispose() {
    _textRecognizer.close();
  }
}
