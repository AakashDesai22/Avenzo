import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_exception.dart';
import '../data/product_lookup_repository.dart';

abstract class ScannerState extends Equatable {
  const ScannerState();

  @override
  List<Object?> get props => [];
}

class ScannerInitial extends ScannerState {}

class ScannerDetecting extends ScannerState {
  final String barcode;
  const ScannerDetecting(this.barcode);

  @override
  List<Object?> get props => [barcode];
}

class ScannerLookingUp extends ScannerState {
  final String barcode;
  const ScannerLookingUp(this.barcode);

  @override
  List<Object?> get props => [barcode];
}

class ScannerProductFound extends ScannerState {
  final String barcode;
  final ProductMasterModel product;
  const ScannerProductFound({required this.barcode, required this.product});

  @override
  List<Object?> get props => [barcode, product];
}

class ScannerProductNotFound extends ScannerState {
  final String barcode;
  const ScannerProductNotFound(this.barcode);

  @override
  List<Object?> get props => [barcode];
}

class ScannerError extends ScannerState {
  final String message;
  final String? barcode;
  const ScannerError({required this.message, this.barcode});

  @override
  List<Object?> get props => [message, barcode];
}

final productLookupRepositoryProvider = Provider<ProductLookupRepository>((ref) {
  return ProductLookupRepository();
});

final scannerNotifierProvider =
    StateNotifierProvider<ScannerNotifier, ScannerState>((ref) {
  return ScannerNotifier(repository: ref.watch(productLookupRepositoryProvider));
});

class ScannerNotifier extends StateNotifier<ScannerState> {
  final ProductLookupRepository _repository;
  String? _lastScannedBarcode;

  ScannerNotifier({required ProductLookupRepository repository})
      : _repository = repository,
        super(ScannerInitial());

  String? get lastScannedBarcode => _lastScannedBarcode;

  Future<void> processBarcode(String rawBarcode) async {
    final cleanBarcode = ProductLookupRepository.normalizeBarcode(rawBarcode);
    if (cleanBarcode.isEmpty) return;

    // Prevent duplicate processing if already looking up or displaying result for same barcode
    if (state is ScannerLookingUp ||
        state is ScannerProductFound ||
        (state is ScannerProductNotFound && (state as ScannerProductNotFound).barcode == cleanBarcode)) {
      return;
    }

    _lastScannedBarcode = cleanBarcode;
    state = ScannerLookingUp(cleanBarcode);

    try {
      final product = await _repository.lookupByBarcode(cleanBarcode);
      if (product != null) {
        state = ScannerProductFound(barcode: cleanBarcode, product: product);
      } else {
        state = ScannerProductNotFound(cleanBarcode);
      }
    } catch (e) {
      final msg = e is ApiException ? e.message : 'Product lookup failed. Please check network connection.';
      state = ScannerError(message: msg, barcode: cleanBarcode);
    }
  }

  void resetScanner() {
    state = ScannerInitial();
  }
}
