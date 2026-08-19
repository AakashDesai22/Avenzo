import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/widgets/avenzo_button.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../providers/ocr_provider.dart';
import 'receipt_review_screen.dart';

/// Screen enabling consumers to capture or pick a receipt photo for OCR ingestion
class ReceiptCaptureScreen extends ConsumerStatefulWidget {
  const ReceiptCaptureScreen({super.key});

  @override
  ConsumerState<ReceiptCaptureScreen> createState() => _ReceiptCaptureScreenState();
}

class _ReceiptCaptureScreenState extends ConsumerState<ReceiptCaptureScreen> {
  File? _selectedImage;
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? picked = await _picker.pickImage(
        source: source,
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 85,
      );
      if (picked != null) {
        setState(() => _selectedImage = File(picked.path));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to pick image: $e')),
        );
      }
    }
  }

  void _processSelectedImage() {
    if (_selectedImage == null) return;
    ref.read(ocrNotifierProvider.notifier).processReceiptImage(_selectedImage!);
  }

  @override
  Widget build(BuildContext context) {
    final ocrState = ref.watch(ocrNotifierProvider);

    ref.listen<OcrState>(ocrNotifierProvider, (previous, next) {
      if (next is OcrReviewReady) {
        ReceiptReviewScreen.show(context, next.result);
      }
    });

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Receipt OCR Ingestion'),
        actions: [
          if (_selectedImage != null)
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              tooltip: 'Reset Image',
              onPressed: () {
                setState(() => _selectedImage = null);
                ref.read(ocrNotifierProvider.notifier).resetOcr();
              },
            ),
        ],
      ),
      body: ocrState is OcrProcessing
          ? const LoadingIndicator(message: 'Processing receipt image with ML Kit OCR...')
          : Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                children: [
                  Expanded(
                    child: Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: _selectedImage != null
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(20),
                              child: Image.file(_selectedImage!, fit: BoxFit.contain),
                            )
                          : Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(24),
                                  decoration: const BoxDecoration(
                                    color: AppColors.primaryLight,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.receipt_long_rounded,
                                    size: 64,
                                    color: AppColors.primary,
                                  ),
                                ),
                                const SizedBox(height: 20),
                                const Text(
                                  'Capture Grocery Receipt',
                                  style: TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                const Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 32.0),
                                  child: Text(
                                    'Take a photo or choose a receipt from your gallery to automatically extract purchased items.',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(fontSize: 14, color: AppColors.textSecondary),
                                  ),
                                ),
                              ],
                            ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  if (_selectedImage == null) ...[
                    Row(
                      children: [
                        Expanded(
                          child: AvenzoButton(
                            text: 'Take Photo',
                            icon: Icons.camera_alt_rounded,
                            onPressed: () => _pickImage(ImageSource.camera),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                            icon: const Icon(Icons.photo_library_rounded, size: 18),
                            label: const Text('Choose Gallery'),
                            onPressed: () => _pickImage(ImageSource.gallery),
                          ),
                        ),
                      ],
                    ),
                  ] else ...[
                    SizedBox(
                      width: double.infinity,
                      child: AvenzoButton(
                        text: 'Process Receipt Photo',
                        icon: Icons.document_scanner_rounded,
                        onPressed: _processSelectedImage,
                      ),
                    ),
                    const SizedBox(height: 10),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.refresh_rounded, size: 18),
                        label: const Text('Choose Different Image'),
                        onPressed: () => _pickImage(ImageSource.gallery),
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}
