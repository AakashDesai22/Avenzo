import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../orders/data/consumer_orders_repository.dart';
import '../../orders/domain/consumer_order_model.dart';

class OrderConfirmationScreen extends ConsumerStatefulWidget {
  final String orderId;

  const OrderConfirmationScreen({super.key, required this.orderId});

  @override
  ConsumerState<OrderConfirmationScreen> createState() => _OrderConfirmationScreenState();
}

class _OrderConfirmationScreenState extends ConsumerState<OrderConfirmationScreen> {
  ConsumerOrderModel? _order;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadOrder();
  }

  Future<void> _loadOrder() async {
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Order Confirmation'),
        automaticallyImplyLeading: false,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null || _order == null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.check_circle_outline, size: 64, color: AppColors.secondary),
                      const SizedBox(height: 16),
                      const Text(
                        'Order Placed Successfully!',
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 20),
                      ElevatedButton(
                        onPressed: () => context.go('/marketplace'),
                        child: const Text('Return to Marketplace'),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      // Success Hero Icon
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: const BoxDecoration(
                          color: AppColors.secondaryLight,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.check_circle_rounded,
                          size: 64,
                          color: AppColors.secondary,
                        ),
                      ),
                      const SizedBox(height: 16),

                      const Text(
                        'Order Placed Successfully!',
                        style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Order #${_order!.orderNumber}',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.primary),
                      ),
                      const SizedBox(height: 24),

                      // Order Overview Card
                      Card(
                        elevation: 0,
                        color: AppColors.surface,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                          side: const BorderSide(color: AppColors.border),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              _ConfirmationRow(label: 'Order Date', value: Formatters.formatDate(_order!.createdAt)),
                              const Divider(height: 16),
                              _ConfirmationRow(label: 'Status', value: _order!.status),
                              const Divider(height: 16),
                              _ConfirmationRow(label: 'Payment Method', value: _order!.paymentMethod),
                              const Divider(height: 16),
                              _ConfirmationRow(label: 'Payment Status', value: _order!.paymentStatus),
                              const Divider(height: 16),
                              _ConfirmationRow(
                                label: 'Total Amount',
                                value: Formatters.currency(_order!.totalAmount),
                                isHighlight: true,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Demo purchase sync banner
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
                        ),
                        child: const Row(
                          children: [
                            Icon(Icons.inventory_2_outlined, color: AppColors.primary, size: 24),
                            SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Demo purchase completed! Stock was deducted using FEFO and your items are now tracked in My Pantry with exact expiry dates.',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: AppColors.textPrimary,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),

                      // CTAs
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () => context.go('/pantry'),
                          icon: const Icon(Icons.kitchen_rounded),
                          label: const Text('Go to My Pantry'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () => context.go('/orders/my/${_order!.id}'),
                          icon: const Icon(Icons.receipt_long),
                          label: const Text('View Order Details'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: TextButton.icon(
                          onPressed: () => context.go('/marketplace'),
                          icon: const Icon(Icons.storefront),
                          label: const Text('Continue Shopping'),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}

class _ConfirmationRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isHighlight;

  const _ConfirmationRow({required this.label, required this.value, this.isHighlight = false});

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
            fontSize: isHighlight ? 15 : 13,
            color: isHighlight ? AppColors.primary : AppColors.textPrimary,
          ),
        ),
      ],
    );
  }
}
