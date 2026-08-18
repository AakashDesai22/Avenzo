import 'package:flutter/material.dart';
import '../../../app/theme/app_colors.dart';

/// Foundation Screen for Scanner
/// (Hardware camera scanning & OCR extraction belong to later milestones)
class ScannerScreenShell extends StatelessWidget {
  const ScannerScreenShell({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Scan Product'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const SizedBox(height: 20),
            // Simulated Viewfinder Frame
            Container(
              height: 280,
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.black87,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.primary, width: 2),
              ),
              child: Stack(
                children: [
                  Center(
                    child: Container(
                      width: 200,
                      height: 140,
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.secondary, width: 2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Center(
                        child: Icon(
                          Icons.qr_code_scanner_rounded,
                          size: 48,
                          color: AppColors.secondary,
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 16,
                    left: 0,
                    right: 0,
                    child: Text(
                      'Position product barcode inside frame',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.8),
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            const Text(
              'Barcode & Label Scanner',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Camera barcode scanning and OCR product label extraction will be enabled in later milestones.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
            const Spacer(),
            OutlinedButton.icon(
              icon: const Icon(Icons.search_rounded),
              label: const Text('Search Product Master Catalogue'),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Catalogue product search active via GET /api/v1/products'),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
