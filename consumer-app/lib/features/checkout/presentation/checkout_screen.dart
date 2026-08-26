import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../cart/providers/cart_provider.dart';
import '../providers/checkout_provider.dart';

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  final _formKey = GlobalKey<FormState>();
  final _addressController = TextEditingController(text: '123 Main Street, Suite 4B, Austin TX 78701');
  final _notesController = TextEditingController();
  String _selectedPaymentMethod = 'MOCK_PAYMENT';

  @override
  void initState() {
    super.initState();
    // Initialize fresh checkout session with Idempotency Key
    Future.microtask(() {
      ref.read(checkoutNotifierProvider.notifier).initCheckout();
    });
  }

  @override
  void dispose() {
    _addressController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  void _onPlaceOrder() async {
    if (!_formKey.currentState!.validate()) return;

    final notifier = ref.read(checkoutNotifierProvider.notifier);
    final order = await notifier.submitCheckout(
      shippingAddress: _addressController.text.trim(),
      notes: _notesController.text.trim().isNotEmpty ? _notesController.text.trim() : null,
      paymentMethod: _selectedPaymentMethod,
    );

    if (mounted && order != null) {
      // Refresh active cart
      ref.read(cartNotifierProvider.notifier).loadCart();
      // Navigate to order confirmation
      context.go('/order-confirmation/${order.id}');
    }
  }

  @override
  Widget build(BuildContext context) {
    final cartState = ref.watch(cartNotifierProvider);
    final checkoutState = ref.watch(checkoutNotifierProvider);
    final cart = cartState.cart;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Checkout', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: cart == null || cart.items.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.shopping_bag_outlined, size: 48, color: AppColors.textSecondary),
                  const SizedBox(height: 12),
                  const Text('No active cart items for checkout.'),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: () => context.go('/marketplace'),
                    child: const Text('Go to Marketplace'),
                  ),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (checkoutState.errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.critical.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppColors.critical),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline, color: AppColors.critical),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                checkoutState.errorMessage!,
                                style: const TextStyle(color: AppColors.critical, fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Shipping Address Field
                    const Text('Shipping Address', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _addressController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: 'Enter complete street address, city, state, zip...',
                        filled: true,
                        fillColor: AppColors.surface,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppColors.border),
                        ),
                      ),
                      validator: (val) {
                        if (val == null || val.trim().length < 5) {
                          return 'Please enter a valid shipping address (at least 5 characters)';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 20),

                    // Delivery Notes Field
                    const Text('Delivery Instructions (Optional)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _notesController,
                      decoration: InputDecoration(
                        hintText: 'e.g. Leave at front door, ring doorbell...',
                        filled: true,
                        fillColor: AppColors.surface,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppColors.border),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Payment Method Selector
                    const Text('Payment Method', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Card(
                      elevation: 0,
                      color: AppColors.surface,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: const BorderSide(color: AppColors.border),
                      ),
                      child: Column(
                        children: [
                          // ignore: deprecated_member_use
                          RadioListTile<String>(
                            title: const Text('Mock Online Payment (Instant Confirmation)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            subtitle: const Text('Simulates instant digital payment processing', style: TextStyle(fontSize: 12)),
                            value: 'MOCK_PAYMENT',
                            // ignore: deprecated_member_use
                            groupValue: _selectedPaymentMethod,
                            // ignore: deprecated_member_use
                            onChanged: (val) => setState(() => _selectedPaymentMethod = val!),
                          ),
                          const Divider(height: 1),
                          // ignore: deprecated_member_use
                          RadioListTile<String>(
                            title: const Text('Cash on Delivery (COD)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            subtitle: const Text('Pay upon package arrival', style: TextStyle(fontSize: 12)),
                            value: 'COD',
                            // ignore: deprecated_member_use
                            groupValue: _selectedPaymentMethod,
                            // ignore: deprecated_member_use
                            onChanged: (val) => setState(() => _selectedPaymentMethod = val!),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Order Items Summary
                    const Text('Order Items', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
                          children: cart.items.map((item) {
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 4),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Text(
                                      '${item.quantity}x ${item.product?.name ?? 'Item'}',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(fontSize: 13),
                                    ),
                                  ),
                                  Text(
                                    Formatters.currency(item.itemTotal),
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Authoritative Pricing Breakdown
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
                                const Text('Subtotal:', style: TextStyle(color: AppColors.textSecondary)),
                                Text(Formatters.currency(cart.calculatedSubtotal), style: const TextStyle(fontWeight: FontWeight.bold)),
                              ],
                            ),
                            const SizedBox(height: 8),
                            const Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text('Estimated Delivery:', style: TextStyle(color: AppColors.textSecondary)),
                                Text('Calculated at order creation', style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 28),

                    // Place Order Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: checkoutState.isSubmitting ? null : _onPlaceOrder,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: checkoutState.isSubmitting
                            ? const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  ),
                                  SizedBox(width: 12),
                                  Text('Placing Order...'),
                                ],
                              )
                            : const Text('Place Order', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
