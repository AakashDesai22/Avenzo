import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/models/pantry_item_model.dart';
import '../../../shared/widgets/error_banner.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../providers/pantry_provider.dart';
import 'add_pantry_item_modal.dart';
import 'pantry_item_detail_sheet.dart';

/// Interactive Production Digital Pantry Screen for Avenzo Consumer App
class PantryScreen extends ConsumerStatefulWidget {
  const PantryScreen({super.key});

  @override
  ConsumerState<PantryScreen> createState() => _PantryScreenState();
}

class _PantryScreenState extends ConsumerState<PantryScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(pantryNotifierProvider.notifier).fetchPantryItems();
    });
  }

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

  @override
  Widget build(BuildContext context) {
    final pantryState = ref.watch(pantryNotifierProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('My Digital Pantry'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
            onPressed: () {
              ref.read(pantryNotifierProvider.notifier).fetchPantryItems();
            },
          ),
          IconButton(
            icon: const Icon(Icons.add_rounded),
            tooltip: 'Add Item',
            onPressed: () => AddPantryItemModal.show(context),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => AddPantryItemModal.show(context),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Add Item'),
      ),
      body: Column(
        children: [
          _buildFilterBar(pantryState),
          Expanded(
            child: _buildContent(context, pantryState),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterBar(PantryState state) {
    String? currentFilter;
    if (state is PantryLoaded) {
      currentFilter = state.activeFilter;
    }

    final filters = [
      {'key': 'all', 'label': 'All Items'},
      {'key': 'pantry', 'label': 'Pantry'},
      {'key': 'fridge', 'label': 'Fridge'},
      {'key': 'freezer', 'label': 'Freezer'},
    ];

    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: filters.map((f) {
            final key = f['key']!;
            final label = f['label']!;
            final isSelected = (currentFilter == null && key == 'all') ||
                (currentFilter == key);

            return Padding(
              padding: const EdgeInsets.only(right: 8.0),
              child: FilterChip(
                selected: isSelected,
                label: Text(label),
                selectedColor: AppColors.primaryLight,
                checkmarkColor: AppColors.primary,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.primary : AppColors.textSecondary,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
                onSelected: (_) {
                  ref.read(pantryNotifierProvider.notifier).setFilter(key);
                },
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context, PantryState state) {
    if (state is PantryLoading || state is PantryInitial) {
      return const LoadingIndicator(message: 'Loading pantry items...');
    }

    if (state is PantryError) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: ErrorBanner(
            message: state.message,
            onRetry: () {
              ref.read(pantryNotifierProvider.notifier).fetchPantryItems();
            },
          ),
        ),
      );
    }

    if (state is PantryLoaded) {
      if (state.items.isEmpty) {
        return _buildEmptyState(context);
      }

      return RefreshIndicator(
        onRefresh: () async {
          await ref.read(pantryNotifierProvider.notifier).fetchPantryItems();
        },
        child: ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: state.items.length,
          itemBuilder: (context, index) {
            final item = state.items[index];
            return _buildPantryItemCard(context, item);
          },
        ),
      );
    }

    return const SizedBox.shrink();
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: const BoxDecoration(
                color: AppColors.primaryLight,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.kitchen_rounded,
                size: 64,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Your Pantry is Empty',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Add your first product or grocery item to start tracking expiry dates and reducing waste.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => AddPantryItemModal.show(context),
              icon: const Icon(Icons.add_rounded),
              label: const Text('Add First Item'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPantryItemCard(BuildContext context, PantryItemModel item) {
    final statusColor = _getExpiryStatusColor(item.expiryStatus);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () => PantryItemDetailSheet.show(context, item),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  item.storageLocation == 'fridge'
                      ? Icons.ac_unit_outlined
                      : (item.storageLocation == 'freezer'
                          ? Icons.severe_cold_outlined
                          : Icons.kitchen_outlined),
                  color: AppColors.primary,
                  size: 24,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.displayName,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${item.quantity} ${item.unit} • ${item.storageLocation.toUpperCase()}',
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  item.formattedDte,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: statusColor,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
