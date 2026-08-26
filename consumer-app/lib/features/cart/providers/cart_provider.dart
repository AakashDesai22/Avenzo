import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/cart_repository.dart';
import '../domain/cart_model.dart';

class CartState extends Equatable {
  final bool isLoading;
  final bool isMutating;
  final CartModel? cart;
  final String? errorMessage;

  const CartState({
    this.isLoading = false,
    this.isMutating = false,
    this.cart,
    this.errorMessage,
  });

  CartState copyWith({
    bool? isLoading,
    bool? isMutating,
    CartModel? cart,
    String? errorMessage,
    bool clearError = false,
  }) {
    return CartState(
      isLoading: isLoading ?? this.isLoading,
      isMutating: isMutating ?? this.isMutating,
      cart: cart ?? this.cart,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }

  int get totalItemCount => cart?.totalItemsCount ?? 0;
  double get subtotal => cart?.calculatedSubtotal ?? 0.0;
  bool get hasItems => cart != null && cart!.items.isNotEmpty;

  @override
  List<Object?> get props => [isLoading, isMutating, cart, errorMessage];
}

final cartNotifierProvider =
    StateNotifierProvider<CartNotifier, CartState>((ref) {
  final repo = ref.watch(cartRepositoryProvider);
  return CartNotifier(repository: repo);
});

class CartNotifier extends StateNotifier<CartState> {
  final CartRepository _repository;

  CartNotifier({required CartRepository repository})
      : _repository = repository,
        super(const CartState()) {
    loadCart();
  }

  /// Loads active consumer shopping cart.
  Future<void> loadCart() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final cart = await _repository.getCart();
      state = state.copyWith(isLoading: false, cart: cart);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Failed to load cart.',
      );
    }
  }

  /// Adds a product to cart.
  Future<bool> addToCart(String productId, {int quantity = 1}) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updatedCart = await _repository.addItem(productId: productId, quantity: quantity);
      state = state.copyWith(isMutating: false, cart: updatedCart);
      return true;
    } catch (e) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'Could not add product to cart.',
      );
      return false;
    }
  }

  /// Updates quantity of an existing cart line item.
  Future<void> updateQuantity(String itemId, int quantity) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updatedCart = await _repository.updateItem(itemId: itemId, quantity: quantity);
      state = state.copyWith(isMutating: false, cart: updatedCart);
    } catch (e) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'Could not update item quantity.',
      );
    }
  }

  /// Removes a line item from cart.
  Future<void> removeItem(String itemId) async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updatedCart = await _repository.removeItem(itemId);
      state = state.copyWith(isMutating: false, cart: updatedCart);
    } catch (e) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'Could not remove item from cart.',
      );
    }
  }

  /// Clears active cart.
  Future<void> clearCart() async {
    state = state.copyWith(isMutating: true, clearError: true);
    try {
      final updatedCart = await _repository.clearCart();
      state = state.copyWith(isMutating: false, cart: updatedCart);
    } catch (e) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'Could not clear cart.',
      );
    }
  }
}
