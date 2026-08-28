import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/models/consumer_analytics_model.dart';
import '../data/analytics_repository.dart';

final analyticsRepositoryProvider = Provider<AnalyticsRepository>((ref) {
  return AnalyticsRepository();
});

class AnalyticsState {
  final bool isLoading;
  final ConsumerWasteMetricsModel? metrics;
  final String? errorMessage;

  const AnalyticsState({
    this.isLoading = false,
    this.metrics,
    this.errorMessage,
  });

  AnalyticsState copyWith({
    bool? isLoading,
    ConsumerWasteMetricsModel? metrics,
    String? errorMessage,
  }) {
    return AnalyticsState(
      isLoading: isLoading ?? this.isLoading,
      metrics: metrics ?? this.metrics,
      errorMessage: errorMessage,
    );
  }
}

class AnalyticsNotifier extends StateNotifier<AnalyticsState> {
  final AnalyticsRepository _repository;

  AnalyticsNotifier(this._repository) : super(const AnalyticsState()) {
    fetchAnalytics();
  }

  Future<void> fetchAnalytics() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final metrics = await _repository.getConsumerWasteAnalytics();
      state = state.copyWith(isLoading: false, metrics: metrics);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }
}

final analyticsNotifierProvider =
    StateNotifierProvider<AnalyticsNotifier, AnalyticsState>((ref) {
  final repo = ref.watch(analyticsRepositoryProvider);
  return AnalyticsNotifier(repo);
});
