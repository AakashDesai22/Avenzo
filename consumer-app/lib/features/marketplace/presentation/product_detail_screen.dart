import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../cart/providers/cart_provider.dart';
import '../data/marketplace_repository.dart';
import '../domain/marketplace_product_model.dart';

class ProductDetailScreen extends ConsumerStatefulWidget {
  final String productId;

  const ProductDetailScreen({super.key, required this.productId});

  @override
  ConsumerState<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends ConsumerState<ProductDetailScreen> {
  MarketplaceProductModel? _product;
  bool _isLoading = true;
  String? _error;
  int _selectedQuantity = 1;

  @override
  void initState() {
    super.initState();
    _loadProduct();
  }

  Future<void> _loadProduct() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final repo = ref.read(marketplaceRepositoryProvider);
      final product = await repo.getProductById(widget.productId);
      setState(() {
        _product = product;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = 'Failed to load product details.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(_product?.name ?? 'Product Details'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null || _product == null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: AppColors.critical),
                      const SizedBox(height: 12),
                      Text(_error ?? 'Product not found.', style: const TextStyle(color: AppColors.textSecondary)),
                      const SizedBox(height: 12),
                      ElevatedButton(onPressed: _loadProduct, child: const Text('Retry')),
                    ],
                  ),
                )
              : Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Product Image Container
                            Container(
                              height: 220,
                              width: double.infinity,
                              decoration: BoxDecoration(
                                color: AppColors.surface,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: AppColors.border),
                              ),
                              child: _product!.imageUrl != null && _product!.imageUrl!.isNotEmpty
                                  ? Image.network(
                                      _product!.imageUrl!,
                                      fit: BoxFit.contain,
                                      errorBuilder: (_, __, ___) => const Icon(
                                        Icons.inventory_2_outlined,
                                        size: 64,
                                        color: AppColors.textSecondary,
                                      ),
                                    )
                                  : const Icon(
                                      Icons.inventory_2_outlined,
                                      size: 64,
                                      color: AppColors.textSecondary,
                                    ),
                            ),
                            const SizedBox(height: 20),

                            // Name & Price Row
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(
                                  child: Text(
                                    _product!.name,
                                    style: const TextStyle(
                                      fontSize: 22,
                                      fontWeight: FontWeight.bold,
                                      color: AppColors.textPrimary,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  Formatters.currency(_product!.unitPrice),
                                  style: const TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.primary,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),

                            // Availability & Category Badges
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: _product!.isAvailable ? AppColors.secondaryLight : AppColors.critical.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    _product!.isAvailable
                                        ? 'In Stock (${_product!.availableQuantity} available)'
                                        : 'Out of Stock',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      color: _product!.isAvailable ? AppColors.secondary : AppColors.critical,
                                    ),
                                  ),
                                ),
                                if (_product!.categoryName != null) ...[
                                  const SizedBox(width: 8),
                                  Chip(
                                    label: Text(_product!.categoryName!, style: const TextStyle(fontSize: 11)),
                                    backgroundColor: AppColors.surface,
                                    side: const BorderSide(color: AppColors.border),
                                  ),
                                ],
                              ],
                            ),
                            const SizedBox(height: 16),

                            // Product Metadata
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
                                    _MetadataRow(label: 'SKU', value: _product!.sku),
                                    const Divider(height: 16),
                                    _MetadataRow(label: 'Unit of Measure', value: _product!.unitOfMeasure),
                                    if (_product!.shelfLifeDays != null) ...[
                                      const Divider(height: 16),
                                      _MetadataRow(
                                          label: 'Shelf Life', value: '${_product!.shelfLifeDays} days'),
                                    ],
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(height: 20),

                            // Description
                            if (_product!.description != null && _product!.description!.isNotEmpty) ...[
                              const Text(
                                'Description',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _product!.description!,
                                style: const TextStyle(color: AppColors.textSecondary, height: 1.5),
                              ),
                              const SizedBox(height: 20),
                            ],

                            // Quantity Selector
                            if (_product!.isAvailable) ...[
                              const Text(
                                'Select Quantity',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  IconButton.outlined(
                                    onPressed: _selectedQuantity > 1
                                        ? () => setState(() => _selectedQuantity--)
                                        : null,
                                    icon: const Icon(Icons.remove),
                                  ),
                                  Padding(
                                    padding: const EdgeInsets.symmetric(horizontal: 16),
                                    child: Text(
                                      '$_selectedQuantity',
                                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                                    ),
                                  ),
                                  IconButton.outlined(
                                    onPressed: _selectedQuantity < _product!.availableQuantity
                                        ? () => setState(() => _selectedQuantity++)
                                        : null,
                                    icon: const Icon(Icons.add),
                                  ),
                                ],
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),

                    // Add to Cart Bottom Bar
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: const BoxDecoration(
                        color: AppColors.surface,
                        border: Border(top: BorderSide(color: AppColors.border)),
                      ),
                      child: SafeArea(
                        child: SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: _product!.isAvailable
                                ? () async {
                                    final success = await ref
                                        .read(cartNotifierProvider.notifier)
                                        .addToCart(_product!.id, quantity: _selectedQuantity);
                                    if (context.mounted && success) {
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        SnackBar(
                                          content: Text('Added $_selectedQuantity x ${_product!.name} to cart!'),
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
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                            child: Text(
                              _product!.isAvailable
                                  ? 'Add to Cart — ${Formatters.currency(_product!.unitPrice * _selectedQuantity)}'
                                  : 'Out of Stock',
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }
}

class _MetadataRow extends StatelessWidget {
  final String label;
  final String value;

  const _MetadataRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
      ],
    );
  }
}
