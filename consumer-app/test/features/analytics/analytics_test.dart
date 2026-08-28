import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/shared/models/consumer_analytics_model.dart';
import 'package:avenzo_consumer/features/analytics/presentation/pantry_analytics_screen.dart';
import 'package:avenzo_consumer/features/analytics/providers/analytics_provider.dart';
import 'package:avenzo_consumer/features/analytics/data/analytics_repository.dart';

void main() {
  group('ConsumerWasteMetricsModel Unit Tests', () {
    test('Correctly parses complete analytics JSON', () {
      final json = {
        'user_id': 'user-123',
        'total_items_tracked': 5,
        'total_items_consumed': 4,
        'total_items_discarded': 1,
        'total_items_expired': 0,
        'consumed_quantity': 10.0,
        'discarded_quantity': 2.0,
        'expired_quantity': 0.0,
        'consumption_ratio': 0.8333,
        'waste_ratio': 0.1667,
        'waste_reduction_score': 83,
        'estimated_money_saved': 45.50,
        'has_sufficient_history': true,
        'history_status': 'Active tracking',
        'top_wasted_categories': [
          {
            'category_name': 'Dairy',
            'discarded_quantity': 2.0,
            'percentage_of_total_waste': 100.0,
          }
        ],
      };

      final model = ConsumerWasteMetricsModel.fromJson(json);

      expect(model.userId, 'user-123');
      expect(model.totalItemsTracked, 5);
      expect(model.consumedQuantity, 10.0);
      expect(model.wasteReductionScore, 83);
      expect(model.estimatedMoneySaved, 45.50);
      expect(model.hasSufficientHistory, isTrue);
      expect(model.topWastedCategories.length, 1);
      expect(model.topWastedCategories.first.categoryName, 'Dairy');
    });

    test('Correctly parses zero-history analytics JSON', () {
      final json = {
        'user_id': 'user-new',
        'total_items_tracked': 0,
        'total_items_consumed': 0,
        'total_items_discarded': 0,
        'total_items_expired': 0,
        'consumed_quantity': 0.0,
        'discarded_quantity': 0.0,
        'expired_quantity': 0.0,
        'consumption_ratio': 0.0,
        'waste_ratio': 0.0,
        'waste_reduction_score': null,
        'estimated_money_saved': 0.0,
        'has_sufficient_history': false,
        'history_status': 'No activity logged yet',
        'top_wasted_categories': [],
      };

      final model = ConsumerWasteMetricsModel.fromJson(json);

      expect(model.userId, 'user-new');
      expect(model.hasSufficientHistory, isFalse);
      expect(model.wasteReductionScore, isNull);
    });
  });

  group('PantryAnalyticsScreen Widget Tests', () {
    testWidgets('Renders onboarding state for zero-history users', (WidgetTester tester) async {
      const zeroHistoryModel = ConsumerWasteMetricsModel(
        userId: 'user-new',
        totalItemsTracked: 0,
        totalItemsConsumed: 0,
        totalItemsDiscarded: 0,
        totalItemsExpired: 0,
        consumedQuantity: 0.0,
        discardedQuantity: 0.0,
        expiredQuantity: 0.0,
        consumptionRatio: 0.0,
        wasteRatio: 0.0,
        wasteReductionScore: null,
        estimatedMoneySaved: 0.0,
        hasSufficientHistory: false,
        historyStatus: 'No activity logged yet',
        topWastedCategories: [],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            analyticsNotifierProvider.overrideWith(
              (ref) => AnalyticsNotifierFake(
                const AnalyticsState(isLoading: false, metrics: zeroHistoryModel),
              ),
            ),
          ],
          child: const MaterialApp(
            home: PantryAnalyticsScreen(),
          ),
        ),
      );

      expect(find.text('Waste Reduction & Insights'), findsOneWidget);
      expect(find.text('Waste Reduction Index'), findsOneWidget);
      expect(find.textContaining('Track more pantry activity'), findsOneWidget);
    });

    testWidgets('Renders Waste Reduction Index score for active user', (WidgetTester tester) async {
      const activeModel = ConsumerWasteMetricsModel(
        userId: 'user-active',
        totalItemsTracked: 5,
        totalItemsConsumed: 4,
        totalItemsDiscarded: 1,
        totalItemsExpired: 0,
        consumedQuantity: 10.0,
        discardedQuantity: 2.0,
        expiredQuantity: 0.0,
        consumptionRatio: 0.8333,
        wasteRatio: 0.1667,
        wasteReductionScore: 83,
        estimatedMoneySaved: 45.50,
        hasSufficientHistory: true,
        historyStatus: 'Active tracking',
        topWastedCategories: [],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            analyticsNotifierProvider.overrideWith(
              (ref) => AnalyticsNotifierFake(
                const AnalyticsState(isLoading: false, metrics: activeModel),
              ),
            ),
          ],
          child: const MaterialApp(
            home: PantryAnalyticsScreen(),
          ),
        ),
      );

      expect(find.text('83 / 100'), findsOneWidget);
      expect(find.text('\$45.50'), findsOneWidget);
    });
  });
}

class AnalyticsNotifierFake extends AnalyticsNotifier {
  AnalyticsNotifierFake(AnalyticsState initialState) : super(AnalyticsRepositoryFake()) {
    state = initialState;
  }

  @override
  Future<void> fetchAnalytics() async {}
}

class AnalyticsRepositoryFake extends AnalyticsRepository {
  @override
  Future<ConsumerWasteMetricsModel> getConsumerWasteAnalytics() async {
    throw UnimplementedError();
  }
}
