import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:avenzo_consumer/features/recommendations/data/recommendation_models.dart';
import 'package:avenzo_consumer/features/recommendations/data/recommendation_repository.dart';
import 'package:avenzo_consumer/features/recommendations/providers/recommendation_provider.dart';
import 'package:avenzo_consumer/features/recommendations/presentation/recommendation_card.dart';
import 'package:avenzo_consumer/features/recommendations/presentation/recommendations_screen.dart';

class MockRecommendationRepository implements RecommendationRepository {
  final List<RecommendationModel> mockRecs;
  final RecommendationSummaryModel mockSummary;

  MockRecommendationRepository({
    required this.mockRecs,
    required this.mockSummary,
  });

  @override
  Future<List<RecommendationModel>> getRecommendations() async => mockRecs;

  @override
  Future<RecommendationSummaryModel> getSummary() async => mockSummary;

  @override
  Future<RecommendationModel> dismissRecommendation(String recommendationId) async {
    return mockRecs.firstWhere((r) => r.id == recommendationId);
  }

  @override
  Future<List<RecommendationModel>> refreshRecommendations() async => mockRecs;
}

void main() {
  final sampleRec = RecommendationModel(
    id: 'rec-1',
    userId: 'user-1',
    pantryItemId: 'item-1',
    recommendationType: 'USE_SOON',
    priority: 'CRITICAL',
    title: 'Use Fresh Milk Soon',
    message: 'Milk expires in 1 day.',
    reason: 'Reaches expiration date on 2026-08-20.',
    suggestedAction: 'Consume or freeze before expiry.',
    isDismissed: false,
    createdAt: DateTime.now(),
  );

  final sampleSummary = const RecommendationSummaryModel(
    totalActiveItems: 5,
    expiring3dCount: 2,
    expiring7dCount: 3,
    estimatedWasteRiskCount: 1,
    hasSufficientHistory: true,
    historyStatus: 'Active usage tracking',
  );

  group('Recommendation Models Unit Tests', () {
    test('RecommendationModel.fromJson parses correctly', () {
      final json = {
        'id': 'rec-123',
        'user_id': 'usr-456',
        'pantry_item_id': 'pantry-789',
        'recommendation_type': 'WASTE_RISK',
        'priority': 'HIGH',
        'title': 'Waste Risk Alert: Spinach',
        'message': 'Spinach expires in 2 days.',
        'reason': 'Historical logs indicate item discard pattern.',
        'suggested_action': 'Cook a spinach dish.',
        'is_dismissed': false,
        'created_at': '2026-08-19T10:00:00.000Z',
      };

      final model = RecommendationModel.fromJson(json);

      expect(model.id, equals('rec-123'));
      expect(model.userId, equals('usr-456'));
      expect(model.recommendationType, equals('WASTE_RISK'));
      expect(model.priority, equals('HIGH'));
      expect(model.title, equals('Waste Risk Alert: Spinach'));
      expect(model.suggestedAction, equals('Cook a spinach dish.'));
      expect(model.isDismissed, isFalse);
    });

    test('RecommendationSummaryModel.fromJson parses correctly', () {
      final json = {
        'total_active_items': 12,
        'expiring_3d_count': 3,
        'expiring_7d_count': 5,
        'estimated_waste_risk_count': 2,
        'has_sufficient_history': true,
        'history_status': 'Active tracking',
      };

      final summary = RecommendationSummaryModel.fromJson(json);

      expect(summary.totalActiveItems, equals(12));
      expect(summary.expiring3dCount, equals(3));
      expect(summary.expiring7dCount, equals(5));
      expect(summary.hasSufficientHistory, isTrue);
    });
  });

  group('RecommendationsNotifier Tests', () {
    test('fetchData populates state with recommendations and summary', () async {
      final mockRepo = MockRecommendationRepository(
        mockRecs: [sampleRec],
        mockSummary: sampleSummary,
      );

      final notifier = RecommendationsNotifier(mockRepo);
      await notifier.fetchData();

      expect(notifier.state.isLoading, isFalse);
      expect(notifier.state.recommendations.length, equals(1));
      expect(notifier.state.recommendations.first.title, equals('Use Fresh Milk Soon'));
      expect(notifier.state.summary?.totalActiveItems, equals(5));
    });

    test('dismissRecommendation removes recommendation from state', () async {
      final mockRepo = MockRecommendationRepository(
        mockRecs: [sampleRec],
        mockSummary: sampleSummary,
      );

      final notifier = RecommendationsNotifier(mockRepo);
      await notifier.fetchData();
      expect(notifier.state.recommendations.length, equals(1));

      await notifier.dismissRecommendation('rec-1');
      expect(notifier.state.recommendations.isEmpty, isTrue);
    });
  });

  group('Recommendation Widgets Tests', () {
    testWidgets('RecommendationCard renders title, priority, reason and action button', (WidgetTester tester) async {
      bool dismissed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RecommendationCard(
              recommendation: sampleRec,
              onDismiss: () => dismissed = true,
            ),
          ),
        ),
      );

      expect(find.text('Use Fresh Milk Soon'), findsOneWidget);
      expect(find.text('Milk expires in 1 day.'), findsOneWidget);
      expect(find.text('CRITICAL'), findsOneWidget);
      expect(find.text('Why: Reaches expiration date on 2026-08-20.'), findsOneWidget);
      expect(find.text('Consume or freeze before expiry.'), findsOneWidget);

      await tester.tap(find.byIcon(Icons.close));
      expect(dismissed, isTrue);
    });

    testWidgets('RecommendationsScreen renders summary and recommendation list', (WidgetTester tester) async {
      final mockRepo = MockRecommendationRepository(
        mockRecs: [sampleRec],
        mockSummary: sampleSummary,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            recommendationRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const MaterialApp(
            home: RecommendationsScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Smart Insights'), findsOneWidget);
      expect(find.text('Pantry Lifecycle Summary'), findsOneWidget);
      expect(find.text('5'), findsOneWidget); // Active items count
      expect(find.text('Use Fresh Milk Soon'), findsOneWidget);
    });
  });
}
