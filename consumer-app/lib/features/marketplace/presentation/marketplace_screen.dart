import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../cart/providers/cart_provider.dart';
import '../domain/marketplace_product_model.dart';
import '../providers/marketplace_provider.dart';

class MarketplaceScreen extends ConsumerWidget {
  const MarketplaceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(marketplaceNotifierProvider);
    final notifier = ref.read(marketplaceNotifierProvider.notifier);
    final cartState = ref.watch(cartNotifierProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(
          'Marketplace',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          Badge(
            isLabelVisible: cartState.totalItemCount > 0,
            label: Text('${cartState.totalItemCount}'),
            child: IconButton(
              icon: const Icon(Icons.shopping_cart_outlined),
              onPressed: () => context.push('/cart'),
              tooltip: 'Shopping Cart',
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              onChanged: notifier.setSearchQuery,
              decoration: InputDecoration(
                hintText: 'Search products by name or SKU...',
                prefixIcon: const Icon(Icons.search, color: AppColors.textSecondary),
                suffixIcon: state.searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 20),
                        onPressed: () => notifier.setSearchQuery(''),
                      )
                    : null,
                filled: true,
                fillColor: AppColors.surface,
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
              ),
            ),
          ),

          // Categories Horizontal Filter Chips
          if (state.categories.isNotEmpty)
            SizedBox(
              height: 38,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: const Text('All'),
                      selected: state.selectedCategoryId == null,
                      onSelected: (_) => notifier.selectCategory(null),
                      selectedColor: AppColors.primaryLight,
                      labelStyle: TextStyle(
                        color: state.selectedCategoryId == null
                            ? AppColors.primary
                            : AppColors.textPrimary,
                        fontWeight: state.selectedCategoryId == null
                            ? FontWeight.bold
                            : FontWeight.normal,
                        fontSize: 13,
                      ),
                    ),
                  ),
                  ...state.categories.map((category) {
                    final isSelected = state.selectedCategoryId == category.id;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(category.name),
                        selected: isSelected,
                        onSelected: (_) => notifier.selectCategory(category.id),
                        selectedColor: AppColors.primaryLight,
                        labelStyle: TextStyle(
                          color: isSelected ? AppColors.primary : AppColors.textPrimary,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          fontSize: 13,
                        ),
                      ),
                    );
                  }),
                ],
              ),
            ),
          if (state.categories.isNotEmpty) const SizedBox(height: 8),

          // Filters Row (In Stock Only)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Row(
              children: [
                FilterChip(
                  label: const Text('In Stock Only'),
                  selected: state.inStockOnly,
                  onSelected: (_) => notifier.toggleInStockOnly(),
                  selectedColor: AppColors.primaryLight,
                  checkmarkColor: AppColors.primary,
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Products List / Grid
          Expanded(
            child: state.isLoading
                ? const Center(child: CircularProgressIndicator())
                : state.isAuthError
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.lock_outline, size: 52, color: AppColors.primary),
                            const SizedBox(height: 16),
                            const Text(
                              'Sign In Required',
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                            ),
                            const SizedBox(height: 8),
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 32),
                              child: Text(
                                state.errorMessage!,
                                textAlign: TextAlign.center,
                                style: const TextStyle(color: AppColors.textSecondary),
                              ),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              onPressed: () => context.push('/login'),
                              icon: const Icon(Icons.login),
                              label: const Text('Sign In'),
                            ),
                          ],
                        ),
                      )
                    : state.isNetworkError
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.wifi_off_outlined, size: 52, color: AppColors.warning),
                                const SizedBox(height: 16),
                                const Text(
                                  'Connection Error',
                                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                                ),
                                const SizedBox(height: 8),
                                Padding(
                                  padding: const EdgeInsets.symmetric(horizontal: 32),
                                  child: Text(
                                    state.errorMessage!,
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(color: AppColors.textSecondary),
                                  ),
                                ),
                                const SizedBox(height: 16),
                                ElevatedButton.icon(
                                  onPressed: notifier.loadProducts,
                                  icon: const Icon(Icons.refresh),
                                  label: const Text('Retry'),
                                ),
                              ],
                            ),
                          )
                        : state.errorMessage != null
                            ? Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
                                    const SizedBox(height: 12),
                                    Text(
                                      state.errorMessage!,
                                      style: const TextStyle(color: AppColors.textSecondary),
                                    ),
                                    const SizedBox(height: 12),
                                    ElevatedButton(
                                      onPressed: notifier.loadProducts,
                                      child: const Text('Retry'),
                                    ),
                                  ],
                                ),
                              )
                            : state.products.isEmpty
                                ? Center(
                                    child: Column(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        const Icon(Icons.shopping_bag_outlined, size: 52, color: AppColors.textSecondary),
                                        const SizedBox(height: 16),
                                        Text(
                                          state.searchQuery.isNotEmpty
                                              ? 'No products matching "${state.searchQuery}"'
                                              : 'No products found matching your search.',
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                            color: AppColors.textPrimary,
                                          ),
                                          textAlign: TextAlign.center,
                                        ),
                                        const SizedBox(height: 8),
                                        const Text(
                                          'Check back soon or try adjusting your search filters.',
                                          style: TextStyle(color: AppColors.textSecondary),
                                        ),
                                        const SizedBox(height: 16),
                                        OutlinedButton.icon(
                                          onPressed: notifier.refresh,
                                          icon: const Icon(Icons.refresh),
                                          label: const Text('Refresh Catalog'),
                                        ),
                                      ],
                                    ),
                                  )
                        : RefreshIndicator(
                            onRefresh: notifier.refresh,
                            child: GridView.builder(
                              padding: const EdgeInsets.all(16),
                              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                crossAxisCount: 2,
                                childAspectRatio: 0.72,
                                crossAxisSpacing: 12,
                                mainAxisSpacing: 12,
                              ),
                              itemCount: state.products.length,
                              itemBuilder: (context, index) {
                                final product = state.products[index];
                                return _ProductCard(product: product);
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}

class _ProductCard extends ConsumerWidget {
  final MarketplaceProductModel product;

  const _ProductCard({required this.product});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return InkWell(
      onTap: () => context.push('/marketplace/product/${product.id}'),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image / Thumbnail
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                ),
                child: product.imageUrl != null && product.imageUrl!.isNotEmpty
                    ? Image.network(
                        product.imageUrl!,
                        fit: BoxFit.cover,
                        loadingBuilder: (context, child, loadingProgress) {
                          if (loadingProgress == null) return child;
                          return Center(
                            child: SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                value: loadingProgress.expectedTotalBytes != null
                                    ? loadingProgress.cumulativeBytesLoaded /
                                        loadingProgress.expectedTotalBytes!
                                    : null,
                              ),
                            ),
                          );
                        },
                        errorBuilder: (_, __, ___) => const Center(
                          child: Icon(
                            Icons.inventory_2_outlined,
                            size: 48,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      )
                    : const Icon(
                        Icons.inventory_2_outlined,
                        size: 48,
                        color: AppColors.textSecondary,
                      ),
              ),
            ),

            // Content
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        Formatters.currency(product.unitPrice),
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                          color: AppColors.primary,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: product.isAvailable ? AppColors.secondaryLight : AppColors.critical.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          product.isAvailable ? 'In Stock' : 'Out of Stock',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: product.isAvailable ? AppColors.secondary : AppColors.critical,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: product.isAvailable
                          ? () async {
                              final success = await ref
                                  .read(cartNotifierProvider.notifier)
                                  .addToCart(product.id, quantity: 1);
                              if (context.mounted && success) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('${product.name} added to cart!'),
                                    duration: const Duration(seconds: 2),
                                    action: SnackBarAction(
                                      label: 'VIEW CART',
                                      onPressed: () => context.push('/cart'),
                                    ),
                                  ),
                                );
                              }
                            }
                          : null,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      child: const Text('Add to Cart', style: TextStyle(fontSize: 12)),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
