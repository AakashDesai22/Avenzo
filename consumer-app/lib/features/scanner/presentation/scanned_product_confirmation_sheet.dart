import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/widgets/avenzo_button.dart';
import '../../pantry/presentation/add_pantry_item_modal.dart';
import '../data/product_lookup_repository.dart';
import '../providers/scanner_provider.dart';

/// Bottom sheet presenting scanned Product Master result with "Add to Pantry" action
class ScannedProductConfirmationSheet extends ConsumerWidget {
  final ProductMasterModel product;

  const ScannedProductConfirmationSheet({super.key, required this.product});

  static Future<void> show(BuildContext context, ProductMasterModel product) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => ScannedProductConfirmationSheet(product: product),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    DateTime? estimatedExpiry;
    if (product.shelfLifeDays != null && product.shelfLifeDays! > 0) {
      estimatedExpiry = DateTime.now().add(Duration(days: product.shelfLifeDays!));
    }

    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: const BoxDecoration(
                  color: AppColors.secondaryLight,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.check_circle_rounded,
                  color: AppColors.secondary,
                  size: 32,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Product Matched!',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppColors.secondary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      product.name,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () {
                  ref.read(scannerNotifierProvider.notifier).resetScanner();
                  Navigator.pop(context);
                },
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (product.brandName != null && product.brandName!.isNotEmpty)
                _buildBadge(product.brandName!, Icons.verified_outlined, AppColors.primary),
              if (product.categoryName != null && product.categoryName!.isNotEmpty)
                _buildBadge(product.categoryName!, Icons.category_outlined, AppColors.info),
              if (product.barcode != null)
                _buildBadge(product.barcode!, Icons.qr_code_rounded, AppColors.textSecondary),
            ],
          ),
          const Divider(height: 32),
          _buildInfoRow(Icons.square_foot_rounded, 'Unit of Measure', product.unitOfMeasure),
          if (product.shelfLifeDays != null)
            _buildInfoRow(Icons.timer_outlined, 'Default Shelf Life', '${product.shelfLifeDays} days'),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: AvenzoButton(
              text: 'Add to Digital Pantry',
              icon: Icons.add_circle_outline,
              onPressed: () {
                Navigator.pop(context);
                ref.read(scannerNotifierProvider.notifier).resetScanner();
                AddPantryItemModal.show(
                  context,
                  initialName: product.name,
                  initialBarcode: product.barcode,
                  initialUnit: product.unitOfMeasure,
                  initialProductId: product.id,
                  initialExpiryDate: estimatedExpiry,
                );
              },
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.qr_code_scanner_rounded, size: 18),
              label: const Text('Scan Another Item'),
              onPressed: () {
                ref.read(scannerNotifierProvider.notifier).resetScanner();
                Navigator.pop(context);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBadge(String label, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10.0),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.textSecondary),
          const SizedBox(width: 10),
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          Text(value, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
        ],
      ),
    );
  }
}
