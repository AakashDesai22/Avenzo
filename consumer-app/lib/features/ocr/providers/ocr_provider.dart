import 'dart:io';
import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../pantry/providers/pantry_provider.dart';
import '../data/ocr_models.dart';
import '../data/ocr_repository.dart';

abstract class OcrState extends Equatable {
  const OcrState();

  @override
  List<Object?> get props => [];
}

class OcrInitial extends OcrState {}

class OcrProcessing extends OcrState {}

class OcrReviewReady extends OcrState {
  final ReceiptOcrResult result;
  const OcrReviewReady(this.result);

  @override
  List<Object?> get props => [result];
}

class OcrIngesting extends OcrState {}

class OcrIngestedSuccess extends OcrState {
  final int count;
  const OcrIngestedSuccess(this.count);

  @override
  List<Object?> get props => [count];
}

class OcrError extends OcrState {
  final String message;
  const OcrError(this.message);

  @override
  List<Object?> get props => [message];
}

final ocrRepositoryProvider = Provider<OcrRepository>((ref) {
  return OcrRepository();
});

final ocrNotifierProvider = StateNotifierProvider<OcrNotifier, OcrState>((ref) {
  return OcrNotifier(repository: ref.watch(ocrRepositoryProvider));
});

class OcrNotifier extends StateNotifier<OcrState> {
  final OcrRepository _repository;

  OcrNotifier({required OcrRepository repository})
      : _repository = repository,
        super(OcrInitial());

  Future<void> processReceiptImage(File imageFile) async {
    state = OcrProcessing();
    try {
      final result = await _repository.processReceiptImage(imageFile);
      state = OcrReviewReady(result);
    } catch (e) {
      state = OcrError('Failed to parse receipt: $e');
    }
  }

  void toggleItemSelection(String itemId) {
    if (state is OcrReviewReady) {
      final current = (state as OcrReviewReady).result;
      final updatedItems = current.items.map((item) {
        if (item.id == itemId) {
          return item.copyWith(isSelected: !item.isSelected);
        }
        return item;
      }).toList();
      state = OcrReviewReady(current.copyWith(items: updatedItems));
    }
  }

  void selectAllItems(bool select) {
    if (state is OcrReviewReady) {
      final current = (state as OcrReviewReady).result;
      final updatedItems = current.items.map((i) => i.copyWith(isSelected: select)).toList();
      state = OcrReviewReady(current.copyWith(items: updatedItems));
    }
  }

  void updateItemName(String itemId, String newName) {
    if (state is OcrReviewReady) {
      final current = (state as OcrReviewReady).result;
      final updatedItems = current.items.map((item) {
        if (item.id == itemId) {
          return item.copyWith(normalizedName: newName, rawName: newName);
        }
        return item;
      }).toList();
      state = OcrReviewReady(current.copyWith(items: updatedItems));
    }
  }

  void updateItemQuantity(String itemId, double newQty) {
    if (state is OcrReviewReady) {
      final current = (state as OcrReviewReady).result;
      final updatedItems = current.items.map((item) {
        if (item.id == itemId) {
          return item.copyWith(quantity: newQty);
        }
        return item;
      }).toList();
      state = OcrReviewReady(current.copyWith(items: updatedItems));
    }
  }

  void removeItem(String itemId) {
    if (state is OcrReviewReady) {
      final current = (state as OcrReviewReady).result;
      final updatedItems = current.items.where((i) => i.id != itemId).toList();
      state = OcrReviewReady(current.copyWith(items: updatedItems));
    }
  }

  void addItemManually(ReceiptOcrItem newItem) {
    if (state is OcrReviewReady) {
      final current = (state as OcrReviewReady).result;
      state = OcrReviewReady(current.copyWith(items: [...current.items, newItem]));
    } else {
      state = OcrReviewReady(ReceiptOcrResult(rawText: newItem.rawName, items: [newItem]));
    }
  }

  Future<bool> ingestSelectedItemsToPantry(
    PantryNotifier pantryNotifier, {
    required String storageLocation,
    DateTime? defaultExpiry,
  }) async {
    if (state is! OcrReviewReady) return false;

    final current = (state as OcrReviewReady).result;
    final selected = current.items.where((i) => i.isSelected).toList();
    if (selected.isEmpty) return false;

    state = OcrIngesting();

    int successCount = 0;
    for (final item in selected) {
      final ok = await pantryNotifier.addItem(
        productId: item.matchedProductId,
        customName: item.normalizedName,
        quantity: item.quantity,
        unit: item.unit,
        storageLocation: storageLocation,
        purchaseDate: current.receiptDate ?? DateTime.now(),
        expiryDate: defaultExpiry ?? DateTime.now().add(const Duration(days: 7)),
        notes: 'Ingested via Receipt OCR (${current.merchantName ?? 'Receipt'})',
      );
      if (ok) successCount++;
    }

    if (successCount > 0) {
      state = OcrIngestedSuccess(successCount);
      return true;
    } else {
      state = OcrError('Failed to ingest items into digital pantry.');
      return false;
    }
  }

  void resetOcr() {
    state = OcrInitial();
  }
}
