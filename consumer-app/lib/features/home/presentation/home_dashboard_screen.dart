import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/utils/formatters.dart';
import '../../auth/providers/auth_provider.dart';
import '../../cart/providers/cart_provider.dart';
import '../../marketplace/domain/category_model.dart';
import '../../marketplace/domain/marketplace_product_model.dart';
import '../../marketplace/providers/marketplace_provider.dart';
import '../../notifications/providers/notification_provider.dart';

/// Consumer Quick-Commerce Inspired Home Screen
/// Combines dynamic catalog discovery with AVENZO's expiry management identity.
class HomeDashboardScreen extends ConsumerWidget {
  const HomeDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);
    final user = authState is Authenticated ? authState.user : null;
    final marketplaceState = ref.watch(marketplaceNotifierProvider);
    final cartState = ref.watch(cartNotifierProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Stack(
          children: [
            RefreshIndicator(
              onRefresh: () async {
                await Future.wait([
                  ref.read(marketplaceNotifierProvider.notifier).refresh(),
                  ref.read(notificationsProvider.notifier).fetchData(),
                  ref.read(cartNotifierProvider.notifier).loadCart(),
                ]);
              },
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. Header (Brand, Location, Action Icons)
                    _HomeHeader(userFirstName: user?.firstName),

                    // 2. Quick Search Bar
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                      child: _QuickSearchBar(
                        onTap: () => context.push('/marketplace'),
                        onScanTap: () => context.go('/home/scan'),
                      ),
                    ),

                    const SizedBox(height: 8),

                    // 3. Dynamic Categories Row
                    _CategoryNavigationSection(
                      categories: marketplaceState.categories,
                      isLoading: marketplaceState.isCategoriesLoading,
                      onCategorySelected: (categoryId) {
                        ref.read(marketplaceNotifierProvider.notifier).selectCategory(categoryId);
                        context.push('/marketplace');
                      },
                      onSeeAll: () {
                        ref.read(marketplaceNotifierProvider.notifier).selectCategory(null);
                        context.push('/marketplace');
                      },
                    ),

                    const SizedBox(height: 16),

                    // 4. AVENZO Value Proposition / Awareness Banner
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16.0),
                      child: _AvenzoPurposeBanner(),
                    ),

                    const SizedBox(height: 16),

                    // 5. Core Expiry & Lifecycle Quick Actions
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16.0),
                      child: Text(
                        'Quick Actions',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16.0),
                      child: _ExpiryQuickActions(),
                    ),

                    const SizedBox(height: 16),

                    // 6. Smart Insights Quick Card
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16.0),
                      child: _SmartInsightsBanner(
                        onTap: () => context.push('/recommendations'),
                      ),
                    ),

                    const SizedBox(height: 24),

                    // 7. Product Discovery Section — Explore Products
                    _ProductDiscoverySection(
                      title: 'Explore Products',
                      subtitle: 'Fresh arrivals with tracked shelf life',
                      isLoading: marketplaceState.isLoading && marketplaceState.products.isEmpty,
                      errorMessage: marketplaceState.errorMessage,
                      products: marketplaceState.products,
                      onRetry: () => ref.read(marketplaceNotifierProvider.notifier).refresh(),
                      onSeeAll: () {
                        ref.read(marketplaceNotifierProvider.notifier).selectCategory(null);
                        context.push('/marketplace');
                      },
                    ),

                    // 8. Category-Based Shelves (if products are categorized)
                    ..._buildCategoryShelves(
                      context: context,
                      ref: ref,
                      categories: marketplaceState.categories,
                      products: marketplaceState.products,
                    ),

                    // Bottom padding to avoid obscuring content with floating cart bar
                    SizedBox(height: cartState.hasItems ? 90 : 24),
                  ],
                ),
              ),
            ),

            // 9. Floating Persistent Cart Summary Bar
            if (cartState.hasItems)
              Positioned(
                bottom: 12,
                left: 16,
                right: 16,
                child: _FloatingCartBar(
                  itemCount: cartState.totalItemCount,
                  subtotal: cartState.subtotal,
                  onTap: () => context.push('/cart'),
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// Builds category-specific horizontal shelves from loaded live catalog data
  List<Widget> _buildCategoryShelves({
    required BuildContext context,
    required WidgetRef ref,
    required List<CategoryModel> categories,
    required List<MarketplaceProductModel> products,
  }) {
    if (products.isEmpty || categories.isEmpty) return [];

    final shelves = <Widget>[];

    // Filter categories that have at least 1 product
    for (final category in categories) {
      final categoryProducts = products.where((p) => p.categoryId == category.id).toList();
      if (categoryProducts.isEmpty) continue;

      shelves.add(const SizedBox(height: 20));
      shelves.add(
        _ProductDiscoverySection(
          title: category.name,
          subtitle: 'Fresh in ${category.name}',
          isLoading: false,
          products: categoryProducts,
          onSeeAll: () {
            ref.read(marketplaceNotifierProvider.notifier).selectCategory(category.id);
            context.push('/marketplace');
          },
        ),
      );

      // Limit to at most 2 category shelves on the home screen for optimal scroll performance
      if (shelves.length >= 4) break;
    }

    return shelves;
  }
}

// ============================================================================
// HEADER WIDGET
// ============================================================================

class _HomeHeader extends StatelessWidget {
  final String? userFirstName;

  const _HomeHeader({this.userFirstName});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Logo & Delivery Location
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(
                        Icons.eco_rounded,
                        color: AppColors.primary,
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      AppConstants.appName,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                        color: AppColors.primaryDark,
                        letterSpacing: 1.2,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(
                      Icons.location_on_rounded,
                      size: 13,
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 4),
                    Flexible(
                      child: Text(
                        userFirstName != null
                            ? 'Deliver to Home • $userFirstName'
                            : 'Deliver to Home',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Action Icons: Analytics, Notifications, Profile
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.analytics_outlined, color: AppColors.textPrimary, size: 22),
                onPressed: () => context.push('/home/analytics'),
                tooltip: 'Waste Analytics & Insights',
              ),
              Consumer(
                builder: (context, ref, child) {
                  final unreadCount = ref.watch(unreadNotificationCountProvider);
                  return Badge(
                    isLabelVisible: unreadCount > 0,
                    label: Text('$unreadCount'),
                    child: IconButton(
                      icon: const Icon(Icons.notifications_outlined, color: AppColors.textPrimary, size: 22),
                      onPressed: () => context.push('/notifications'),
                      tooltip: 'Notifications',
                    ),
                  );
                },
              ),
              IconButton(
                icon: const Icon(Icons.person_outline_rounded, color: AppColors.textPrimary, size: 24),
                onPressed: () => context.go('/home/profile'),
                tooltip: 'My Profile',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// QUICK SEARCH BAR WIDGET
// ============================================================================

class _QuickSearchBar extends StatelessWidget {
  final VoidCallback onTap;
  final VoidCallback onScanTap;

  const _QuickSearchBar({
    required this.onTap,
    required this.onScanTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const Icon(Icons.search_rounded, color: AppColors.primary, size: 22),
            const SizedBox(width: 10),
            const Expanded(
              child: Text(
                'Search fresh groceries, dairy, produce...',
                style: TextStyle(
                  fontSize: 13,
                  color: AppColors.textMuted,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Container(
              height: 20,
              width: 1,
              color: AppColors.border,
              margin: const EdgeInsets.symmetric(horizontal: 8),
            ),
            IconButton(
              icon: const Icon(Icons.qr_code_scanner_rounded, color: AppColors.primary, size: 20),
              onPressed: onScanTap,
              tooltip: 'Scan Barcode',
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// CATEGORY NAVIGATION ROW
// ============================================================================

class _CategoryNavigationSection extends StatelessWidget {
  final List<CategoryModel> categories;
  final bool isLoading;
  final ValueChanged<String?> onCategorySelected;
  final VoidCallback onSeeAll;

  const _CategoryNavigationSection({
    required this.categories,
    required this.isLoading,
    required this.onCategorySelected,
    required this.onSeeAll,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Shop by Category',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              InkWell(
                onTap: onSeeAll,
                borderRadius: BorderRadius.circular(6),
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  child: Text(
                    'See All',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        SizedBox(
          height: 94,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            children: [
              // All Categories Tile
              _CategoryItemTile(
                name: 'All',
                icon: Icons.grid_view_rounded,
                color: AppColors.primary,
                onTap: () => onCategorySelected(null),
              ),
              // Backend Categories
              ...categories.map((category) {
                final iconData = _mapCategoryIcon(category.name);
                return _CategoryItemTile(
                  name: category.name,
                  icon: iconData,
                  color: _mapCategoryColor(category.name),
                  onTap: () => onCategorySelected(category.id),
                );
              }),
            ],
          ),
        ),
      ],
    );
  }

  static IconData _mapCategoryIcon(String categoryName) {
    final lower = categoryName.toLowerCase();
    if (lower.contains('dairy') || lower.contains('milk') || lower.contains('egg')) {
      return Icons.egg_alt_rounded;
    }
    if (lower.contains('bakery') || lower.contains('bread')) {
      return Icons.bakery_dining_rounded;
    }
    if (lower.contains('produce') || lower.contains('fruit') || lower.contains('veg')) {
      return Icons.eco_rounded;
    }
    if (lower.contains('beverage') || lower.contains('drink') || lower.contains('juice') || lower.contains('tea')) {
      return Icons.local_cafe_rounded;
    }
    if (lower.contains('snack') || lower.contains('cookie') || lower.contains('chip')) {
      return Icons.cookie_rounded;
    }
    if (lower.contains('meat') || lower.contains('fish') || lower.contains('chicken')) {
      return Icons.set_meal_rounded;
    }
    if (lower.contains('pantry') || lower.contains('spice') || lower.contains('oil') || lower.contains('rice')) {
      return Icons.kitchen_rounded;
    }
    return Icons.category_rounded;
  }

  static Color _mapCategoryColor(String categoryName) {
    final lower = categoryName.toLowerCase();
    if (lower.contains('dairy') || lower.contains('milk')) {
      return const Color(0xFF0284C7); // Sky Blue
    }
    if (lower.contains('bakery') || lower.contains('bread')) {
      return const Color(0xFFD97706); // Amber
    }
    if (lower.contains('produce') || lower.contains('veg')) {
      return const Color(0xFF059669); // Emerald
    }
    if (lower.contains('beverage') || lower.contains('drink')) {
      return const Color(0xFF7C3AED); // Purple
    }
    return AppColors.primary;
  }
}

class _CategoryItemTile extends StatelessWidget {
  final String name;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _CategoryItemTile({
    required this.name,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 72,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Column(
          children: [
            Container(
              width: 54,
              height: 54,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: color.withValues(alpha: 0.2)),
              ),
              child: Icon(icon, color: color, size: 26),
            ),
            const SizedBox(height: 6),
            Text(
              name,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// AVENZO PURPOSE / BRAND VALUE BANNER
// ============================================================================

class _AvenzoPurposeBanner extends StatelessWidget {
  const _AvenzoPurposeBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primaryDark, AppColors.primary],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withValues(alpha: 0.25),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    'ZERO WASTE • SMART LIFECYCLE',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Fresh Groceries with Guaranteed Shelf Life',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Every item is tracked from inventory to pantry to prevent food waste.',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.white70,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.shopping_bag_rounded,
              color: Colors.white,
              size: 32,
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// CORE EXPIRY & LIFECYCLE QUICK ACTIONS
// ============================================================================

class _ExpiryQuickActions extends StatelessWidget {
  const _ExpiryQuickActions();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _ActionTile(
            title: 'Scan Product',
            subtitle: 'Barcode Lookup',
            icon: Icons.qr_code_scanner_rounded,
            color: AppColors.primary,
            onTap: () => context.go('/home/scan'),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _ActionTile(
            title: 'My Pantry',
            subtitle: 'Digital Stock',
            icon: Icons.kitchen_rounded,
            color: AppColors.secondary,
            onTap: () => context.go('/home/pantry'),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _ActionTile(
            title: 'Expiring Soon',
            subtitle: 'Waste Alerts',
            icon: Icons.timer_rounded,
            color: AppColors.warning,
            onTap: () => context.go('/home/expiring'),
          ),
        ),
      ],
    );
  }
}

class _ActionTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _ActionTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(height: 6),
            Text(
              title,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 2),
            Text(
              subtitle,
              style: const TextStyle(
                fontSize: 9,
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// SMART INSIGHTS CARD
// ============================================================================

class _SmartInsightsBanner extends StatelessWidget {
  final VoidCallback onTap;

  const _SmartInsightsBanner({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: Colors.indigo.shade200),
      ),
      color: Colors.indigo.shade50,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: const BoxDecoration(
            color: Colors.indigo,
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.auto_awesome, color: Colors.white, size: 18),
        ),
        title: const Text(
          'Smart Insights & Recommendations',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary),
        ),
        subtitle: const Text(
          'Personalized expiry reduction suggestions',
          style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
        ),
        trailing: const Icon(Icons.chevron_right, color: Colors.indigo, size: 20),
        onTap: onTap,
      ),
    );
  }
}

// ============================================================================
// PRODUCT DISCOVERY SHELF (QUICK COMMERCE HORIZONTAL ROW)
// ============================================================================

class _ProductDiscoverySection extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool isLoading;
  final String? errorMessage;
  final List<MarketplaceProductModel> products;
  final VoidCallback? onRetry;
  final VoidCallback onSeeAll;

  const _ProductDiscoverySection({
    required this.title,
    required this.subtitle,
    this.isLoading = false,
    this.errorMessage,
    required this.products,
    this.onRetry,
    required this.onSeeAll,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section Header
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              InkWell(
                onTap: onSeeAll,
                borderRadius: BorderRadius.circular(6),
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  child: Text(
                    'See All',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        if (isLoading)
          SizedBox(
            height: 220,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: 3,
              itemBuilder: (context, index) => Container(
                width: 148,
                margin: const EdgeInsets.symmetric(horizontal: 4),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  children: [
                    Container(
                      height: 96,
                      decoration: const BoxDecoration(
                        color: AppColors.surfaceVariant,
                        borderRadius: BorderRadius.vertical(top: Radius.circular(13)),
                      ),
                      child: const Center(
                        child: Icon(Icons.inventory_2_outlined, color: AppColors.textMuted, size: 32),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            height: 12,
                            width: 100,
                            decoration: BoxDecoration(
                              color: AppColors.surfaceVariant,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Container(
                            height: 10,
                            width: 50,
                            decoration: BoxDecoration(
                              color: AppColors.surfaceVariant,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          )
        else if (errorMessage != null && products.isEmpty)
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              children: [
                const Icon(Icons.info_outline, color: AppColors.critical, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    errorMessage!,
                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
                ),
                if (onRetry != null)
                  TextButton(
                    onPressed: onRetry,
                    child: const Text('Retry'),
                  ),
              ],
            ),
          )
        else if (products.isEmpty)
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: const Row(
              children: [
                Icon(Icons.inventory_2_outlined, color: AppColors.textMuted, size: 20),
                SizedBox(width: 8),
                Text(
                  'No items available in this section right now.',
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          )
        else
          SizedBox(
            height: 220,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: products.length,
              itemBuilder: (context, index) {
                final product = products[index];
                return _QuickCommerceProductCard(product: product);
              },
            ),
          ),
      ],
    );
  }
}

// ============================================================================
// QUICK COMMERCE PRODUCT CARD WIDGET
// ============================================================================

class _QuickCommerceProductCard extends ConsumerWidget {
  final MarketplaceProductModel product;

  const _QuickCommerceProductCard({required this.product});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      width: 148,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () => context.push('/marketplace/product/${product.id}'),
        borderRadius: BorderRadius.circular(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image Box & Overlays
            Stack(
              children: [
                Container(
                  height: 96,
                  width: double.infinity,
                  decoration: const BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.vertical(top: Radius.circular(13)),
                  ),
                  child: product.imageUrl != null && product.imageUrl!.isNotEmpty
                      ? Image.network(
                          product.imageUrl!,
                          fit: BoxFit.cover,
                          loadingBuilder: (context, child, loadingProgress) {
                            if (loadingProgress == null) return child;
                            return Center(
                              child: SizedBox(
                                width: 20,
                                height: 20,
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
                              size: 36,
                              color: AppColors.textMuted,
                            ),
                          ),
                        )
                      : const Center(
                          child: Icon(
                            Icons.inventory_2_outlined,
                            size: 36,
                            color: AppColors.textMuted,
                          ),
                        ),
                ),
                // Expiry / Stock Badge Overlay
                Positioned(
                  top: 6,
                  left: 6,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: product.isAvailable
                          ? (product.hasExpiry && product.shelfLifeDays != null
                              ? AppColors.primaryLight
                              : AppColors.secondaryLight)
                          : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      product.isAvailable
                          ? (product.hasExpiry && product.shelfLifeDays != null
                              ? '${product.shelfLifeDays}d shelf life'
                              : 'In Stock')
                          : 'Out of Stock',
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                        color: product.isAvailable
                            ? (product.hasExpiry && product.shelfLifeDays != null
                                ? AppColors.primaryDark
                                : AppColors.safe)
                            : AppColors.textMuted,
                      ),
                    ),
                  ),
                ),
              ],
            ),

            // Product Details & Add Button
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          product.name,
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AppColors.textPrimary,
                            height: 1.2,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          product.unitOfMeasure,
                          style: const TextStyle(
                            fontSize: 10,
                            color: AppColors.textMuted,
                          ),
                        ),
                      ],
                    ),

                    // Price & Add to Cart Action
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Flexible(
                          child: Text(
                            Formatters.currency(product.unitPrice),
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textPrimary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 4),
                        if (product.isAvailable)
                          InkWell(
                            onTap: () {
                              ref.read(cartNotifierProvider.notifier).addToCart(
                                    product.id,
                                    quantity: 1,
                                  );
                              ScaffoldMessenger.of(context).hideCurrentSnackBar();
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('${product.name} added to cart'),
                                  duration: const Duration(seconds: 2),
                                  behavior: SnackBarBehavior.floating,
                                ),
                              );
                            },
                            borderRadius: BorderRadius.circular(6),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.primaryLight,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: AppColors.primary),
                              ),
                              child: const Text(
                                '+ ADD',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.primary,
                                ),
                              ),
                            ),
                          )
                        else
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade100,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              'Unavailable',
                              style: TextStyle(
                                fontSize: 9,
                                color: AppColors.textMuted,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// FLOATING QUICK COMMERCE CART BAR
// ============================================================================

class _FloatingCartBar extends StatelessWidget {
  final int itemCount;
  final double subtotal;
  final VoidCallback onTap;

  const _FloatingCartBar({
    required this.itemCount,
    required this.subtotal,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      elevation: 6,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppColors.primaryDark, AppColors.primary],
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
            ),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.35),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.2),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.shopping_bag_outlined,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '$itemCount ${itemCount == 1 ? 'item' : 'items'} in cart',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        Formatters.currency(subtotal),
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Colors.white70,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const Row(
                children: [
                  Text(
                    'View Cart',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(width: 4),
                  Icon(
                    Icons.arrow_forward_rounded,
                    color: Colors.white,
                    size: 18,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
