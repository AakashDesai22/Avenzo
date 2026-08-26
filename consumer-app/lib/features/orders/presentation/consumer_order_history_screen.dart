import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../providers/consumer_orders_provider.dart';

class ConsumerOrderHistoryScreen extends ConsumerWidget {
  const ConsumerOrderHistoryScreen({super.key});

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
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(consumerOrdersNotifierProvider);
    final notifier = ref.read(consumerOrdersNotifierProvider.notifier);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('My Purchase Orders', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: state.isLoading
          ? const Center(child: CircularProgressIndicator())
          : state.errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
                      const SizedBox(height: 12),
                      Text(state.errorMessage!, style: const TextStyle(color: AppColors.textSecondary)),
                      const SizedBox(height: 12),
                      ElevatedButton(onPressed: notifier.loadMyOrders, child: const Text('Retry')),
                    ],
                  ),
                )
              : state.orders.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.receipt_long_outlined, size: 64, color: AppColors.textSecondary),
                          const SizedBox(height: 16),
                          const Text('No orders placed yet', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          const Text('Explore marketplace products and place your first order.', style: TextStyle(color: AppColors.textSecondary)),
                          const SizedBox(height: 20),
                          ElevatedButton.icon(
                            onPressed: () => context.go('/marketplace'),
                            icon: const Icon(Icons.storefront),
                            label: const Text('Start Shopping'),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: notifier.loadMyOrders,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: state.orders.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 12),
                        itemBuilder: (context, index) {
                          final order = state.orders[index];
                          final statusColor = _getStatusColor(order.status);

                          return InkWell(
                            onTap: () => context.push('/orders/my/${order.id}'),
                            borderRadius: BorderRadius.circular(12),
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: AppColors.surface,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: AppColors.border),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        'Order #${order.orderNumber}',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppColors.primary),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: statusColor.withValues(alpha: 0.12),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          order.status,
                                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: statusColor),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        Formatters.formatDate(order.createdAt),
                                        style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                                      ),
                                      Text(
                                        Formatters.currency(order.totalAmount),
                                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    '${order.items.length} item(s) • ${order.paymentMethod}',
                                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
