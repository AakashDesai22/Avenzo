import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/recommendation_models.dart';
import '../data/recommendation_repository.dart';

final recommendationRepositoryProvider = Provider<RecommendationRepository>((ref) {
  return RecommendationRepository();
});

class RecommendationsState {
  final bool isLoading;
  final List<RecommendationModel> recommendations;
  final RecommendationSummaryModel? summary;
  final String? errorMessage;

  const RecommendationsState({
    this.isLoading = false,
    this.recommendations = const [],
    this.summary,
    this.errorMessage,
  });

  RecommendationsState copyWith({
    bool? isLoading,
    List<RecommendationModel>? recommendations,
    RecommendationSummaryModel? summary,
    String? errorMessage,
  }) {
    return RecommendationsState(
      isLoading: isLoading ?? this.isLoading,
      recommendations: recommendations ?? this.recommendations,
      summary: summary ?? this.summary,
      errorMessage: errorMessage,
    );
  }
}

class RecommendationsNotifier extends StateNotifier<RecommendationsState> {
  final RecommendationRepository _repository;

  RecommendationsNotifier(this._repository) : super(const RecommendationsState()) {
    fetchData();
  }

  Future<void> fetchData() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final results = await Future.wait([
        _repository.getRecommendations(),
        _repository.getSummary(),
      ]);

      state = state.copyWith(
        isLoading: false,
        recommendations: results[0] as List<RecommendationModel>,
        summary: results[1] as RecommendationSummaryModel,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }

  Future<void> dismissRecommendation(String recommendationId) async {
    final updatedList = state.recommendations
        .where((r) => r.id != recommendationId)
        .toList();
    state = state.copyWith(recommendations: updatedList);

    try {
      await _repository.dismissRecommendation(recommendationId);
    } catch (e) {
      // Revert on failure
      fetchData();
    }
  }

  Future<void> refresh() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final updatedRecs = await _repository.refreshRecommendations();
      final summary = await _repository.getSummary();
      state = state.copyWith(
        isLoading: false,
        recommendations: updatedRecs,
        summary: summary,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }
}

final recommendationsProvider =
    StateNotifierProvider<RecommendationsNotifier, RecommendationsState>((ref) {
  final repo = ref.watch(recommendationRepositoryProvider);
  return RecommendationsNotifier(repo);
});
