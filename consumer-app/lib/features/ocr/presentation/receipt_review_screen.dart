import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/widgets/avenzo_button.dart';
import '../../pantry/providers/pantry_provider.dart';
import '../data/ocr_models.dart';
import '../providers/ocr_provider.dart';

/// Interactive Material 3 Review Screen for extracted receipt line-items
class ReceiptReviewScreen extends ConsumerStatefulWidget {
  final ReceiptOcrResult result;

  const ReceiptReviewScreen({super.key, required this.result});

  static Future<void> show(BuildContext context, ReceiptOcrResult result) {
    return Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => ReceiptReviewScreen(result: result)),
    );
  }

  @override
  ConsumerState<ReceiptReviewScreen> createState() => _ReceiptReviewScreenState();
}

class _ReceiptReviewScreenState extends ConsumerState<ReceiptReviewScreen> {
  String _storageLocation = 'pantry'; // pantry, fridge, freezer
  DateTime _defaultExpiry = DateTime.now().add(const Duration(days: 7));
  bool _isSubmitting = false;

  Future<void> _selectExpiryDate(BuildContext context) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _defaultExpiry,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() => _defaultExpiry = picked);
    }
  }

  Color _getMatchStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'MATCHED':
        return AppColors.safe;
      case 'SUGGESTED':
        return AppColors.warning;
      case 'UNMATCHED':
      default:
        return AppColors.textSecondary;
    }
  }

  Future<void> _submitIngestion() async {
    final state = ref.read(ocrNotifierProvider);
    if (state is! OcrReviewReady) return;

    final selectedCount = state.result.items.where((i) => i.isSelected).length;
    if (selectedCount == 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one item to add to pantry.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final pantryNotifier = ref.read(pantryNotifierProvider.notifier);
    final success = await ref.read(ocrNotifierProvider.notifier).ingestSelectedItemsToPantry(
          pantryNotifier,
          storageLocation: _storageLocation,
          defaultExpiry: _defaultExpiry,
        );

    if (mounted) {
      setState(() => _isSubmitting = false);
      if (success) {
        Navigator.pop(context); // Return to previous screen
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$selectedCount items added to Digital Pantry successfully!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to ingest items. Please try again.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ocrState = ref.watch(ocrNotifierProvider);
    final currentResult = (ocrState is OcrReviewReady) ? ocrState.result : widget.result;
    final selectedCount = currentResult.items.where((i) => i.isSelected).length;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Review Scanned Receipt'),
        actions: [
          TextButton(
            onPressed: () {
              final allSelected = currentResult.items.every((i) => i.isSelected);
              ref.read(ocrNotifierProvider.notifier).selectAllItems(!allSelected);
            },
            child: Text(
              currentResult.items.every((i) => i.isSelected) ? 'Deselect All' : 'Select All',
              style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(16),
        decoration: const BoxDecoration(
          color: AppColors.surface,
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: SafeArea(
          child: AvenzoButton(
            text: 'Add $selectedCount Items to Pantry',
            icon: Icons.add_circle_outline,
            isLoading: _isSubmitting || ocrState is OcrIngesting,
            onPressed: selectedCount > 0 ? _submitIngestion : null,
          ),
        ),
      ),
      body: Column(
        children: [
          // Receipt Summary Banner
          Container(
            color: AppColors.surface,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            currentResult.merchantName ?? 'Grocery Store',
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Date: ${DateFormat.yMMMd().format(currentResult.receiptDate ?? DateTime.now())}',
                            style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                    ),
                    if (currentResult.totalAmount != null)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppColors.primaryLight,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'Total: \$${currentResult.totalAmount!.toStringAsFixed(2)}',
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.primary),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 16),

                // Ingestion Controls (Storage Location & Default Expiry)
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Storage Location', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 4),
                          DropdownButtonFormField<String>(
                            initialValue: _storageLocation,
                            decoration: const InputDecoration(contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                            items: const [
                              DropdownMenuItem(value: 'pantry', child: Text('Pantry')),
                              DropdownMenuItem(value: 'fridge', child: Text('Fridge')),
                              DropdownMenuItem(value: 'freezer', child: Text('Freezer')),
                            ],
                            onChanged: (val) {
                              if (val != null) setState(() => _storageLocation = val);
                            },
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Default Expiry', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 4),
                          OutlinedButton.icon(
                            onPressed: () => _selectExpiryDate(context),
                            icon: const Icon(Icons.event, size: 16),
                            label: Text(
                              DateFormat('MMM d').format(_defaultExpiry),
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Detected Line Items List
          Expanded(
            child: currentResult.items.isEmpty
                ? const Center(child: Text('No product items detected on this receipt.'))
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: currentResult.items.length,
                    itemBuilder: (context, index) {
                      final item = currentResult.items[index];
                      return _buildItemCard(context, item);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildItemCard(BuildContext context, ReceiptOcrItem item) {
    final statusColor = _getMatchStatusColor(item.matchStatus);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          children: [
            Checkbox(
              value: item.isSelected,
              activeColor: AppColors.primary,
              onChanged: (_) {
                ref.read(ocrNotifierProvider.notifier).toggleItemSelection(item.id);
              },
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.normalizedName,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: item.isSelected ? AppColors.textPrimary : AppColors.textMuted,
                      decoration: item.isSelected ? null : TextDecoration.lineThrough,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text(
                        'Qty: ${item.quantity} ${item.unit}',
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                      if (item.totalPrice != null) ...[
                        const Text(' • ', style: TextStyle(color: AppColors.textMuted)),
                        Text(
                          '\$${item.totalPrice!.toStringAsFixed(2)}',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.primary),
                        ),
                      ],
                    ],
                  ),
                  if (item.matchedProductName != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Matched: ${item.matchedProductName}',
                      style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: AppColors.primary),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: statusColor.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                item.matchStatus,
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: statusColor),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.textMuted),
              onPressed: () {
                ref.read(ocrNotifierProvider.notifier).removeItem(item.id);
              },
            ),
          ],
        ),
      ),
    );
  }
}
