import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/widgets/avenzo_button.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../pantry/presentation/add_pantry_item_modal.dart';
import '../providers/scanner_provider.dart';
import 'scanned_product_confirmation_sheet.dart';

/// Real Device Camera Barcode Scanner Screen for Avenzo Consumer App
class ScannerScreen extends ConsumerStatefulWidget {
  const ScannerScreen({super.key});

  @override
  ConsumerState<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends ConsumerState<ScannerScreen> with WidgetsBindingObserver {
  late final MobileScannerController _controller;
  bool _isTorchOn = false;
  bool _hasPermissionError = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _controller = MobileScannerController(
      detectionSpeed: DetectionSpeed.noDuplicates,
      formats: const [
        BarcodeFormat.ean13,
        BarcodeFormat.ean8,
        BarcodeFormat.upcA,
        BarcodeFormat.upcE,
        BarcodeFormat.code128,
        BarcodeFormat.code39,
        BarcodeFormat.qrCode,
      ],
    );
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _controller.start();
    } else if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive) {
      _controller.stop();
    }
  }

  void _onDetect(BarcodeCapture capture) {
    final barcodes = capture.barcodes;
    if (barcodes.isEmpty) return;

    final rawVal = barcodes.first.rawValue;
    if (rawVal != null && rawVal.trim().isNotEmpty) {
      ref.read(scannerNotifierProvider.notifier).processBarcode(rawVal);
    }
  }

  void _toggleTorch() {
    _controller.toggleTorch();
    setState(() => _isTorchOn = !_isTorchOn);
  }

  void _showProductNotFoundSheet(BuildContext context, String barcode) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                color: AppColors.primaryLight,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.search_off_rounded, color: AppColors.primary, size: 36),
            ),
            const SizedBox(height: 16),
            const Text(
              'Product Not Found',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 6),
            Text(
              'Barcode "$barcode" is not yet registered in Avenzo Product Master.',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 14, color: AppColors.textSecondary),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: AvenzoButton(
                text: 'Enter Product Manually',
                icon: Icons.edit_note_rounded,
                onPressed: () {
                  Navigator.pop(ctx);
                  ref.read(scannerNotifierProvider.notifier).resetScanner();
                  AddPantryItemModal.show(context, initialBarcode: barcode);
                },
              ),
            ),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.qr_code_scanner_rounded, size: 18),
                label: const Text('Scan Again'),
                onPressed: () {
                  ref.read(scannerNotifierProvider.notifier).resetScanner();
                  Navigator.pop(ctx);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scannerState = ref.watch(scannerNotifierProvider);

    // Listen to Scanner state transitions for modal triggers
    ref.listen<ScannerState>(scannerNotifierProvider, (previous, next) {
      if (next is ScannerProductFound) {
        ScannedProductConfirmationSheet.show(context, next.product);
      } else if (next is ScannerProductNotFound) {
        _showProductNotFoundSheet(context, next.barcode);
      }
    });

    if (_hasPermissionError) {
      return _buildPermissionDeniedUI(context);
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Real Camera Scanner Preview
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
            errorBuilder: (context, error, child) {
              return _buildPermissionDeniedUI(context);
            },
          ),

          // Scan Frame / Target Guide Overlay
          Center(
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.primary, width: 3),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.qr_code_scanner_rounded, color: Colors.white70, size: 48),
                  SizedBox(height: 8),
                  Text(
                    'Align Barcode in Frame',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ],
              ),
            ),
          ),

          // Header Overlay Controls
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
                  ),
                  const Text(
                    'Scan Product Barcode',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  IconButton(
                    icon: Icon(
                      _isTorchOn ? Icons.flash_on_rounded : Icons.flash_off_rounded,
                      color: _isTorchOn ? Colors.amber : Colors.white,
                    ),
                    onPressed: _toggleTorch,
                  ),
                ],
              ),
            ),
          ),

          // Looking Up Overlay Banner
          if (scannerState is ScannerLookingUp)
            Container(
              color: Colors.black.withValues(alpha: 0.7),
              child: const Center(
                child: LoadingIndicator(message: 'Looking up barcode in Avenzo Product Master...'),
              ),
            ),

          // Error State Overlay Banner
          if (scannerState is ScannerError)
            Positioned(
              bottom: 30,
              left: 20,
              right: 20,
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.critical),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      scannerState.message,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.critical, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        if (scannerState.barcode != null)
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () {
                                ref.read(scannerNotifierProvider.notifier).processBarcode(scannerState.barcode!);
                              },
                              child: const Text('Try Again'),
                            ),
                          ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () {
                              ref.read(scannerNotifierProvider.notifier).resetScanner();
                            },
                            child: const Text('Scan Again'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildPermissionDeniedUI(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Camera Permission Required')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: AppColors.critical.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.camera_alt_outlined, size: 64, color: AppColors.critical),
              ),
              const SizedBox(height: 20),
              const Text(
                'Camera Access Denied',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
              ),
              const SizedBox(height: 8),
              const Text(
                'Avenzo requires camera permission to scan product barcodes directly into your pantry.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () {
                  _controller.start();
                  setState(() => _hasPermissionError = false);
                },
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry Permission'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
