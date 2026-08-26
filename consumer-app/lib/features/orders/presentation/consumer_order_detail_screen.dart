import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../data/consumer_orders_repository.dart';
import '../domain/consumer_order_model.dart';
import '../providers/consumer_orders_provider.dart';

class ConsumerOrderDetailScreen extends ConsumerStatefulWidget {
  final String orderId;

  const ConsumerOrderDetailScreen({super.key, required this.orderId});

  @override
  ConsumerState<ConsumerOrderDetailScreen> createState() => _ConsumerOrderDetailScreenState();
}

class _ConsumerOrderDetailScreenState extends ConsumerState<ConsumerOrderDetailScreen> {
  ConsumerOrderModel? _order;
  bool _isLoading = true;
  bool _isCancelling = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadOrderDetail();
  }

  Future<void> _loadOrderDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final repo = ref.read(consumerOrdersRepositoryProvider);
      final order = await repo.getMyOrderById(widget.orderId);
      setState(() {
        _order = order;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = 'Failed to load order details.';
      });
    }
  }

  void _onCancelOrder() async {
    if (_order == null) return;

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Order?'),
        content: Text('Are you sure you want to cancel Order #${_order!.orderNumber}? Stock reservations will be released.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('NO, KEEP ORDER')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.critical),
            child: const Text('YES, CANCEL ORDER'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    setState(() => _isCancelling = true);
    final success = await ref.read(consumerOrdersNotifierProvider.notifier).cancelOrder(_order!.id);
    setState(() => _isCancelling = false);

    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Order cancelled successfully.')),
        );
        _loadOrderDetail();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not cancel order. It may have already been dispatched.')),
        );
      }
    }
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'PENDING':
        return Colors.orange.shade700;
      case 'CONFIRMED':
        return Colors.blue.shade700;
      case 'ALLOCATED':
        return Colors.indigo.shade700;
      case 'PACKED':
        return Colors.purple.shade700;
      case 'SHIPPED':
        return Colors.cyan.shade700;
      case 'DELIVERED':
        return Colors.green.shade700;
      case 'CANCELLED':
      case 'FAILED':
        return Colors.red.shade700;
      default:
        return AppColors.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(_order != null ? 'Order #${_order!.orderNumber}' : 'Order Details'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null || _order == null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
                      const SizedBox(height: 12),
                      Text(_error ?? 'Order not found.', style: const TextStyle(color: AppColors.textSecondary)),
                      const SizedBox(height: 12),
                      ElevatedButton(onPressed: _loadOrderDetail, child: const Text('Retry')),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header Summary Card
                      Card(
                        elevation: 0,
                        color: AppColors.surface,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: const BorderSide(color: AppColors.border),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'Order #${_order!.orderNumber}',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: _getStatusColor(_order!.status).withValues(alpha: 0.12),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      _order!.status,
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.bold,
                                        color: _getStatusColor(_order!.status),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const Divider(height: 20),
                              _DetailRow(label: 'Order Date', value: Formatters.formatDate(_order!.createdAt)),
                              const SizedBox(height: 8),
                              _DetailRow(label: 'Payment Method', value: _order!.paymentMethod),
                              const SizedBox(height: 8),
                              _DetailRow(label: 'Payment Status', value: _order!.paymentStatus),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Shipping Address Card
                      const Text('Shipping Address', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Card(
                        elevation: 0,
                        color: AppColors.surface,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: const BorderSide(color: AppColors.border),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(_order!.shippingAddress, style: const TextStyle(fontSize: 14, height: 1.4)),
                              if (_order!.notes != null && _order!.notes!.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Text(
                                  'Notes: ${_order!.notes}',
                                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, fontStyle: FontStyle.italic),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Line Items Table
                      const Text('Order Line Items', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Card(
                        elevation: 0,
                        color: AppColors.surface,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: const BorderSide(color: AppColors.border),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            children: _order!.items.map<Widget>((item) {
                              return Container(
                                padding: const EdgeInsets.symmetric(vertical: 8),
                                decoration: const BoxDecoration(
                                  border: Border(bottom: BorderSide(color: AppColors.border, width: 0.5)),
                                ),
                                child: Row(
                                  children: [
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            item.product?.name ?? 'Product Item',
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            '${item.quantity}x @ ${Formatters.currency(item.unitPrice)}',
                                            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                          ),
                                        ],
                                      ),
                                    ),
                                    Text(
                                      Formatters.currency(item.totalPrice),
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary),
                                    ),
                                  ],
                                ),
                              );
                            }).toList(),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Authoritative Financial Summary
                      Card(
                        elevation: 0,
                        color: AppColors.surface,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: const BorderSide(color: AppColors.border),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              _DetailRow(label: 'Subtotal', value: Formatters.currency(_order!.subtotal)),
                              const SizedBox(height: 8),
                              _DetailRow(label: 'Delivery Fee', value: Formatters.currency(_order!.deliveryFee)),
                              const Divider(height: 20),
                              _DetailRow(
                                label: 'Grand Total',
                                value: Formatters.currency(_order!.totalAmount),
                                isHighlight: true,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Pre-shipment Order Cancellation Control
                      if (_order!.canCancel) ...[
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: _isCancelling ? null : _onCancelOrder,
                            icon: const Icon(Icons.cancel_outlined, color: AppColors.critical),
                            label: Text(
                              _isCancelling ? 'Cancelling Order...' : 'Cancel Order',
                              style: const TextStyle(color: AppColors.critical, fontWeight: FontWeight.bold),
                            ),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              side: const BorderSide(color: AppColors.critical),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],
                    ],
                  ),
                ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isHighlight;

  const _DetailRow({required this.label, required this.value, this.isHighlight = false});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: isHighlight ? 16 : 13,
            color: isHighlight ? AppColors.primary : AppColors.textPrimary,
          ),
        ),
      ],
    );
  }
}
