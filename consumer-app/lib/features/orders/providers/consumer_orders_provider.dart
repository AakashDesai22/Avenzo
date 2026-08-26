import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/consumer_orders_repository.dart';
import '../domain/consumer_order_model.dart';

class ConsumerOrdersState extends Equatable {
  final bool isLoading;
  final List<ConsumerOrderModel> orders;
  final ConsumerOrderModel? selectedOrder;
  final String? errorMessage;

  const ConsumerOrdersState({
    this.isLoading = false,
    this.orders = const [],
    this.selectedOrder,
    this.errorMessage,
  });

  ConsumerOrdersState copyWith({
    bool? isLoading,
    List<ConsumerOrderModel>? orders,
    ConsumerOrderModel? selectedOrder,
    bool clearSelected = false,
    String? errorMessage,
    bool clearError = false,
  }) {
    return ConsumerOrdersState(
      isLoading: isLoading ?? this.isLoading,
      orders: orders ?? this.orders,
      selectedOrder: clearSelected ? null : (selectedOrder ?? this.selectedOrder),
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }

  @override
  List<Object?> get props => [isLoading, orders, selectedOrder, errorMessage];
}

final consumerOrdersNotifierProvider =
    StateNotifierProvider<ConsumerOrdersNotifier, ConsumerOrdersState>((ref) {
  final repo = ref.watch(consumerOrdersRepositoryProvider);
  return ConsumerOrdersNotifier(repository: repo);
});

class ConsumerOrdersNotifier extends StateNotifier<ConsumerOrdersState> {
  final ConsumerOrdersRepository _repository;

  ConsumerOrdersNotifier({required ConsumerOrdersRepository repository})
      : _repository = repository,
        super(const ConsumerOrdersState()) {
    loadMyOrders();
  }

  /// Loads consumer order history.
  Future<void> loadMyOrders() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final list = await _repository.getMyOrders();
      state = state.copyWith(isLoading: false, orders: list);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Failed to load order history.',
      );
    }
  }

  /// Loads order details by ID.
  Future<void> loadOrderDetail(String orderId) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final order = await _repository.getMyOrderById(orderId);
      state = state.copyWith(isLoading: false, selectedOrder: order);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Failed to load order details.',
      );
    }
  }

  /// Cancels an order pre-shipment.
  Future<bool> cancelOrder(String orderId) async {
    try {
      final updatedOrder = await _repository.cancelOrder(orderId);
      state = state.copyWith(
        selectedOrder: updatedOrder,
        orders: state.orders.map((o) => o.id == orderId ? updatedOrder : o).toList(),
      );
      return true;
    } catch (e) {
      state = state.copyWith(errorMessage: 'Could not cancel order.');
      return false;
    }
  }
}
