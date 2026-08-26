import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/models/pantry_item_model.dart';
import '../../../shared/widgets/avenzo_button.dart';
import '../providers/pantry_provider.dart';

/// Modal bottom sheet displaying Pantry Item details and Consume/Discard/Delete actions
class PantryItemDetailSheet extends ConsumerStatefulWidget {
  final PantryItemModel item;

  const PantryItemDetailSheet({super.key, required this.item});

  static Future<void> show(BuildContext context, PantryItemModel item) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => PantryItemDetailSheet(item: item),
    );
  }

  @override
  ConsumerState<PantryItemDetailSheet> createState() => _PantryItemDetailSheetState();
}

class _PantryItemDetailSheetState extends ConsumerState<PantryItemDetailSheet> {
  bool _isActionLoading = false;

  Color _getExpiryStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'SAFE':
        return AppColors.safe;
      case 'EXPIRING_SOON':
        return AppColors.warning;
      case 'CRITICAL':
        return AppColors.critical;
      case 'EXPIRED':
        return const Color(0xFF991B1B);
      default:
        return AppColors.textSecondary;
    }
  }

  Future<void> _showConsumeDialog() async {
    final qtyController = TextEditingController(text: widget.item.quantity.toString());
    final result = await showDialog<double>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Consume ${widget.item.displayName}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Available stock: ${widget.item.quantity} ${widget.item.unit}'),
            const SizedBox(height: 12),
            TextField(
              controller: qtyController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                labelText: 'Quantity to Consume',
                suffixText: widget.item.unit,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final val = double.tryParse(qtyController.text.trim());
              if (val != null && val > 0 && val <= widget.item.quantity) {
                Navigator.pop(context, val);
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Invalid quantity entered.')),
                );
              }
            },
            child: const Text('Consume'),
          ),
        ],
      ),
    );

    if (result != null && mounted) {
      setState(() => _isActionLoading = true);
      final success = await ref.read(pantryNotifierProvider.notifier).consumeItem(
            widget.item.id,
            result,
          );
      if (mounted) {
        setState(() => _isActionLoading = false);
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(success
                ? 'Consumed $result ${widget.item.unit} of ${widget.item.displayName}'
                : 'Failed to consume item.'),
          ),
        );
      }
    }
  }

  Future<void> _showDiscardDialog() async {
    final qtyController = TextEditingController(text: widget.item.quantity.toString());
    final result = await showDialog<double>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Discard/Waste ${widget.item.displayName}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Available stock: ${widget.item.quantity} ${widget.item.unit}'),
            const SizedBox(height: 12),
            TextField(
              controller: qtyController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                labelText: 'Quantity to Discard',
                suffixText: widget.item.unit,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.critical),
            onPressed: () {
              final val = double.tryParse(qtyController.text.trim());
              if (val != null && val > 0 && val <= widget.item.quantity) {
                Navigator.pop(context, val);
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Invalid quantity entered.')),
                );
              }
            },
            child: const Text('Discard'),
          ),
        ],
      ),
    );

    if (result != null && mounted) {
      setState(() => _isActionLoading = true);
      final success = await ref.read(pantryNotifierProvider.notifier).discardItem(
            widget.item.id,
            result,
          );
      if (mounted) {
        setState(() => _isActionLoading = false);
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(success
                ? 'Discarded $result ${widget.item.unit} of ${widget.item.displayName}'
                : 'Failed to discard item.'),
          ),
        );
      }
    }
  }

  Future<void> _showDeleteConfirmation() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Pantry Item'),
        content: Text('Are you sure you want to remove "${widget.item.displayName}" from your pantry?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.critical),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirm == true && mounted) {
      setState(() => _isActionLoading = true);
      final success = await ref.read(pantryNotifierProvider.notifier).deleteItem(widget.item.id);
      if (mounted) {
        setState(() => _isActionLoading = false);
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(success ? 'Item deleted from pantry.' : 'Failed to delete item.'),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getExpiryStatusColor(widget.item.expiryStatus);

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
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.item.displayName,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${widget.item.quantity} ${widget.item.unit}',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (widget.item.isRecalled) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF2F2),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFFCA5A5)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.warning_amber_rounded, color: Color(0xFF991B1B), size: 20),
                      SizedBox(width: 8),
                      Text(
                        'MANUFACTURER SAFETY RECALL',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF991B1B),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    widget.item.recallReason ?? 'This product batch has been recalled for safety reasons. Please do not consume.',
                    style: const TextStyle(
                      fontSize: 13,
                      color: Color(0xFF7F1D1D),
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _buildBadge(
                label: widget.item.storageLocation.toUpperCase(),
                icon: widget.item.storageLocation == 'fridge'
                    ? Icons.ac_unit_outlined
                    : (widget.item.storageLocation == 'freezer'
                        ? Icons.severe_cold_outlined
                        : Icons.kitchen_outlined),
                color: AppColors.primary,
                bgColor: AppColors.primaryLight,
              ),
              _buildBadge(
                label: widget.item.formattedDte,
                icon: widget.item.isRecalled ? Icons.warning_amber_rounded : Icons.timer_outlined,
                color: widget.item.isRecalled ? const Color(0xFF991B1B) : statusColor,
                bgColor: (widget.item.isRecalled ? const Color(0xFF991B1B) : statusColor).withValues(alpha: 0.12),
              ),
            ],
          ),
          const Divider(height: 32),
          if (widget.item.batchNumber != null && widget.item.batchNumber!.isNotEmpty)
            _buildDetailRow(Icons.pin_outlined, 'Batch Number', widget.item.batchNumber!),
          _buildDetailRow(Icons.event_outlined, 'Expiry Date', widget.item.formattedExpiry),
          if (widget.item.barcode != null && widget.item.barcode!.isNotEmpty)
            _buildDetailRow(Icons.qr_code_rounded, 'Barcode', widget.item.barcode!),
          if (widget.item.notes != null && widget.item.notes!.isNotEmpty)
            _buildDetailRow(Icons.notes_rounded, 'Notes', widget.item.notes!),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: AvenzoButton(
                  text: 'Consume',
                  icon: Icons.check_circle_outline,
                  isLoading: _isActionLoading,
                  onPressed: _showConsumeDialog,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: AvenzoButton(
                  text: 'Discard',
                  icon: Icons.delete_sweep_outlined,
                  backgroundColor: AppColors.warning,
                  isLoading: _isActionLoading,
                  onPressed: _showDiscardDialog,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.critical,
                side: const BorderSide(color: AppColors.critical),
              ),
              icon: const Icon(Icons.delete_outline, size: 18),
              label: const Text('Delete from Pantry'),
              onPressed: _isActionLoading ? null : _showDeleteConfirmation,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBadge({
    required String label,
    required IconData icon,
    required Color color,
    required Color bgColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: bgColor,
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

  Widget _buildDetailRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.textSecondary),
          const SizedBox(width: 10),
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
          ),
        ],
      ),
    );
  }
}
