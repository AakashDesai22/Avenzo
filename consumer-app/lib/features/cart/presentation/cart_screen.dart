import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../domain/cart_model.dart';
import '../providers/cart_provider.dart';

class CartScreen extends ConsumerWidget {
  const CartScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cartState = ref.watch(cartNotifierProvider);
    final cartNotifier = ref.read(cartNotifierProvider.notifier);

    final cart = cartState.cart;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('My Shopping Cart', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          if (cartState.hasItems)
            TextButton.icon(
              onPressed: () async {
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Clear Cart?'),
                    content: const Text('Are you sure you want to remove all items from your cart?'),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('CANCEL')),
                      TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('CLEAR')),
                    ],
                  ),
                );
                if (confirm == true) {
                  cartNotifier.clearCart();
                }
              },
              icon: const Icon(Icons.delete_sweep, color: AppColors.critical, size: 20),
              label: const Text('Clear', style: TextStyle(color: AppColors.critical)),
            ),
        ],
      ),
      body: cartState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : cart == null || cart.items.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.remove_shopping_cart_outlined, size: 64, color: AppColors.textSecondary),
                      const SizedBox(height: 16),
                      const Text(
                        'Your cart is empty',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Explore the marketplace and discover fresh products.',
                        style: TextStyle(color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 20),
                      ElevatedButton.icon(
                        onPressed: () => context.go('/marketplace'),
                        icon: const Icon(Icons.storefront),
                        label: const Text('Browse Marketplace'),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    // Stock Warning Banner if items unavailable
                    if (cart.hasUnavailableItems)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        color: AppColors.critical.withValues(alpha: 0.12),
                        child: const Row(
                          children: [
                            Icon(Icons.warning_amber_rounded, color: AppColors.critical, size: 22),
                            SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                'Some items in your cart are no longer available in the requested quantity. Please update your cart before checkout.',
                                style: TextStyle(color: AppColors.critical, fontSize: 12, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                      ),

                    // Cart Items List
                    Expanded(
                      child: RefreshIndicator(
                        onRefresh: cartNotifier.loadCart,
                        child: ListView.separated(
                          padding: const EdgeInsets.all(16),
                          itemCount: cart.items.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            final item = cart.items[index];
                            return _CartItemTile(item: item);
                          },
                        ),
                      ),
                    ),

                    // Subtotal & Checkout Bottom Bar
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: const BoxDecoration(
                        color: AppColors.surface,
                        border: Border(top: BorderSide(color: AppColors.border)),
                      ),
                      child: SafeArea(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text('Subtotal:', style: TextStyle(fontSize: 16, color: AppColors.textSecondary)),
                                Text(
                                  Formatters.currency(cart.calculatedSubtotal),
                                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.primary),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: !cart.hasUnavailableItems
                                    ? () => context.push('/checkout')
                                    : null,
                                style: ElevatedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(vertical: 14),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                ),
                                child: const Text('Proceed to Checkout', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }
}

class _CartItemTile extends ConsumerWidget {
  final CartItemModel item;

  const _CartItemTile({required this.item});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(cartNotifierProvider.notifier);
    final product = item.product;

    final isItemUnavailable = product == null || !product.isAvailable || item.quantity > product.availableQuantity;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isItemUnavailable ? AppColors.critical : AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image Thumbnail
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.background,
              borderRadius: BorderRadius.circular(8),
            ),
            child: product?.imageUrl != null && product!.imageUrl!.isNotEmpty
                ? Image.network(
                    product.imageUrl!,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const Icon(Icons.inventory_2_outlined, color: AppColors.textSecondary),
                  )
                : const Icon(Icons.inventory_2_outlined, color: AppColors.textSecondary),
          ),
          const SizedBox(width: 12),

          // Details & Controls
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  product?.name ?? 'Product Item',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary),
                ),
                const SizedBox(height: 2),
                Text(
                  Formatters.currency(product?.unitPrice ?? 0.0),
                  style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                ),
                if (isItemUnavailable) ...[
                  const SizedBox(height: 4),
                  Text(
                    product == null || !product.isAvailable
                        ? 'Product currently unavailable'
                        : 'Max available: ${product.availableQuantity}',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.critical),
                  ),
                ],
                const SizedBox(height: 8),

                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Quantity Control Buttons
                    Row(
                      children: [
                        IconButton.outlined(
                          constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                          padding: EdgeInsets.zero,
                          icon: const Icon(Icons.remove, size: 16),
                          onPressed: () {
                            if (item.quantity > 1) {
                              notifier.updateQuantity(item.id, item.quantity - 1);
                            } else {
                              notifier.removeItem(item.id);
                            }
                          },
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 10),
                          child: Text(
                            '${item.quantity}',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                        ),
                        IconButton.outlined(
                          constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                          padding: EdgeInsets.zero,
                          icon: const Icon(Icons.add, size: 16),
                          onPressed: () {
                            notifier.updateQuantity(item.id, item.quantity + 1);
                          },
                        ),
                      ],
                    ),

                    // Total & Delete
                    Row(
                      children: [
                        Text(
                          Formatters.currency(item.itemTotal),
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, color: AppColors.textSecondary, size: 20),
                          onPressed: () => notifier.removeItem(item.id),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
