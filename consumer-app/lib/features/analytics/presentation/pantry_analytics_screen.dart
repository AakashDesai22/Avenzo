import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../app/theme/app_colors.dart';
import '../providers/analytics_provider.dart';

class PantryAnalyticsScreen extends ConsumerWidget {
  const PantryAnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(analyticsNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Waste Reduction & Insights', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(analyticsNotifierProvider.notifier).fetchAnalytics(),
            tooltip: 'Refresh Insights',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(analyticsNotifierProvider.notifier).fetchAnalytics(),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (state.isLoading)
                const Padding(
                  padding: EdgeInsets.all(48.0),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (state.errorMessage != null)
                Card(
                  color: Colors.red.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      children: [
                        Icon(Icons.error_outline, color: Colors.red.shade700, size: 36),
                        const SizedBox(height: 8),
                        Text(state.errorMessage!, textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: () => ref.read(analyticsNotifierProvider.notifier).fetchAnalytics(),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              else if (state.metrics != null) ...[
                _buildScoreHeader(context, state.metrics!),
                const SizedBox(height: 16),
                _buildMetricsGrid(context, state.metrics!),
                const SizedBox(height: 16),
                _buildTopCategoriesCard(context, state.metrics!),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildScoreHeader(BuildContext context, dynamic metrics) {
    final hasHistory = metrics.hasSufficientHistory == true && metrics.wasteReductionScore != null;
    final score = metrics.wasteReductionScore ?? 0;

    Color scoreColor = AppColors.primary;
    if (hasHistory) {
      if (score >= 80) {
        scoreColor = AppColors.safe;
      } else if (score >= 60) {
        scoreColor = AppColors.warning;
      } else {
        scoreColor = AppColors.critical;
      }
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: scoreColor.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    hasHistory ? Icons.eco_rounded : Icons.insights_rounded,
                    color: scoreColor,
                    size: 32,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Waste Reduction Index',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        metrics.historyStatus,
                        style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
                if (hasHistory)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: scoreColor,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '$score / 100',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ),
              ],
            ),
            if (!hasHistory) ...[
              const Divider(height: 24),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.info_outline, color: AppColors.primary, size: 20),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Track more pantry activity (consume or discard items) to calculate your Waste Reduction Index.',
                        style: TextStyle(fontSize: 12, color: AppColors.primary, height: 1.3),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMetricsGrid(BuildContext context, dynamic metrics) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.45,
      children: [
        _buildStatCard(
          title: 'Items Consumed',
          value: '${metrics.totalItemsConsumed}',
          subText: '${metrics.consumedQuantity.toStringAsFixed(1)} units used',
          icon: Icons.check_circle_outline,
          color: AppColors.safe,
        ),
        _buildStatCard(
          title: 'Items Wasted',
          value: '${metrics.totalItemsDiscarded + metrics.totalItemsExpired}',
          subText: '${(metrics.discardedQuantity + metrics.expiredQuantity).toStringAsFixed(1)} units wasted',
          icon: Icons.delete_sweep_outlined,
          color: AppColors.critical,
        ),
        _buildStatCard(
          title: 'Consumption Ratio',
          value: '${(metrics.consumptionRatio * 100).toStringAsFixed(0)}%',
          subText: 'Products fully used',
          icon: Icons.pie_chart_outline,
          color: AppColors.primary,
        ),
        _buildStatCard(
          title: 'Est. Money Saved',
          value: '\$${metrics.estimatedMoneySaved.toStringAsFixed(2)}',
          subText: 'Saved from waste',
          icon: Icons.savings_outlined,
          color: AppColors.safe,
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required String title,
    required String value,
    required String subText,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color),
            ),
            const SizedBox(height: 2),
            Text(
              subText,
              style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopCategoriesCard(BuildContext context, dynamic metrics) {
    final categories = metrics.topWastedCategories as List;

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Top Wasted Product Categories',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 12),
            if (categories.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 16.0),
                child: Center(
                  child: Text(
                    'No waste reported across categories. Excellent job!',
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                  ),
                ),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: categories.length,
                separatorBuilder: (context, index) => const Divider(height: 16),
                itemBuilder: (context, index) {
                  final cat = categories[index];
                  return Row(
                    children: [
                      const Icon(Icons.label_outlined, size: 18, color: AppColors.primary),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          cat.categoryName,
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                        ),
                      ),
                      Text(
                        '${cat.discardedQuantity.toStringAsFixed(1)} units (${cat.percentageOfTotalWaste.toStringAsFixed(0)}%)',
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.critical),
                      ),
                    ],
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}
