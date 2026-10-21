import 'dart:async';
import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/marketplace_repository.dart';
import '../domain/category_model.dart';
import '../domain/marketplace_product_model.dart';

class MarketplaceState extends Equatable {
  final bool isLoading;
  final bool isCategoriesLoading;
  final List<MarketplaceProductModel> products;
  final List<CategoryModel> categories;
  final String searchQuery;
  final String? selectedCategoryId;
  final bool inStockOnly;
  final String? errorMessage;

  const MarketplaceState({
    this.isLoading = false,
    this.isCategoriesLoading = false,
    this.products = const [],
    this.categories = const [],
    this.searchQuery = '',
    this.selectedCategoryId,
    this.inStockOnly = false,
    this.errorMessage,
  });

  MarketplaceState copyWith({
    bool? isLoading,
    bool? isCategoriesLoading,
    List<MarketplaceProductModel>? products,
    List<CategoryModel>? categories,
    String? searchQuery,
    String? selectedCategoryId,
    bool clearCategory = false,
    bool? inStockOnly,
    String? errorMessage,
    bool clearError = false,
  }) {
    return MarketplaceState(
      isLoading: isLoading ?? this.isLoading,
      isCategoriesLoading: isCategoriesLoading ?? this.isCategoriesLoading,
      products: products ?? this.products,
      categories: categories ?? this.categories,
      searchQuery: searchQuery ?? this.searchQuery,
      selectedCategoryId: clearCategory ? null : (selectedCategoryId ?? this.selectedCategoryId),
      inStockOnly: inStockOnly ?? this.inStockOnly,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }

  @override
  List<Object?> get props => [
        isLoading,
        isCategoriesLoading,
        products,
        categories,
        searchQuery,
        selectedCategoryId,
        inStockOnly,
        errorMessage,
      ];
}

final marketplaceNotifierProvider =
    StateNotifierProvider<MarketplaceNotifier, MarketplaceState>((ref) {
  final repo = ref.watch(marketplaceRepositoryProvider);
  return MarketplaceNotifier(repository: repo);
});

class MarketplaceNotifier extends StateNotifier<MarketplaceState> {
  final MarketplaceRepository _repository;
  Timer? _debounceTimer;

  MarketplaceNotifier({required MarketplaceRepository repository})
      : _repository = repository,
        super(const MarketplaceState()) {
    loadCategories();
    loadProducts();
  }

  /// Loads active categories for marketplace filtering.
  Future<void> loadCategories() async {
    state = state.copyWith(isCategoriesLoading: true);
    try {
      final list = await _repository.getCategories();
      state = state.copyWith(isCategoriesLoading: false, categories: list);
    } catch (_) {
      state = state.copyWith(isCategoriesLoading: false);
    }
  }

  /// Loads marketplace products with active state filters.
  Future<void> loadProducts() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final list = await _repository.getProducts(
        categoryId: state.selectedCategoryId,
        search: state.searchQuery,
        inStockOnly: state.inStockOnly,
      );
      state = state.copyWith(isLoading: false, products: list);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Failed to load products. Please check your connection.',
      );
    }
  }

  /// Refreshes both categories and product catalog (used by pull-to-refresh).
  Future<void> refresh() async {
    await Future.wait([
      loadCategories(),
      loadProducts(),
    ]);
  }

  /// Updates search query with 300ms debounce.
  void setSearchQuery(String query) {
    if (state.searchQuery == query) return;
    state = state.copyWith(searchQuery: query);

    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      loadProducts();
    });
  }

  /// Filters by category ID (toggles selection if same category clicked).
  void selectCategory(String? categoryId) {
    if (state.selectedCategoryId == categoryId) {
      state = state.copyWith(clearCategory: true);
    } else {
      state = state.copyWith(selectedCategoryId: categoryId);
    }
    loadProducts();
  }

  /// Toggles in-stock only filter.
  void toggleInStockOnly() {
    state = state.copyWith(inStockOnly: !state.inStockOnly);
    loadProducts();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }
}

