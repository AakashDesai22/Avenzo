import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/utils/uuid_generator.dart';
import '../../orders/domain/consumer_order_model.dart';
import '../data/checkout_repository.dart';

class CheckoutState extends Equatable {
  final bool isSubmitting;
  final String idempotencyKey;
  final ConsumerOrderModel? createdOrder;
  final String? errorMessage;

  const CheckoutState({
    this.isSubmitting = false,
    required this.idempotencyKey,
    this.createdOrder,
    this.errorMessage,
  });

  CheckoutState copyWith({
    bool? isSubmitting,
    String? idempotencyKey,
    ConsumerOrderModel? createdOrder,
    String? errorMessage,
    bool clearError = false,
  }) {
    return CheckoutState(
      isSubmitting: isSubmitting ?? this.isSubmitting,
      idempotencyKey: idempotencyKey ?? this.idempotencyKey,
      createdOrder: createdOrder ?? this.createdOrder,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }

  @override
  List<Object?> get props => [isSubmitting, idempotencyKey, createdOrder, errorMessage];
}

final checkoutNotifierProvider =
    StateNotifierProvider<CheckoutNotifier, CheckoutState>((ref) {
  final repo = ref.watch(checkoutRepositoryProvider);
  return CheckoutNotifier(repository: repo);
});

class CheckoutNotifier extends StateNotifier<CheckoutState> {
  final CheckoutRepository _repository;

  CheckoutNotifier({required CheckoutRepository repository})
      : _repository = repository,
        super(CheckoutState(idempotencyKey: UuidGenerator.generateV4()));

  /// Initializes a new checkout session with a fresh Idempotency-Key.
  void initCheckout() {
    state = CheckoutState(idempotencyKey: UuidGenerator.generateV4());
  }

  /// Submits checkout request using active Idempotency-Key.
  Future<ConsumerOrderModel?> submitCheckout({
    required String shippingAddress,
    String? notes,
    String paymentMethod = 'MOCK_PAYMENT',
  }) async {
    if (state.isSubmitting) return null;

    state = state.copyWith(isSubmitting: true, clearError: true);
    try {
      final order = await _repository.checkout(
        shippingAddress: shippingAddress,
        notes: notes,
        paymentMethod: paymentMethod,
        idempotencyKey: state.idempotencyKey,
      );

      state = state.copyWith(
        isSubmitting: false,
        createdOrder: order,
      );
      return order;
    } catch (e) {
      final message = e.toString().contains('400')
          ? 'Stock or validation error during checkout. Please verify item availability in cart.'
          : 'Checkout failed. Please check your network connection and retry.';

      state = state.copyWith(
        isSubmitting: false,
        errorMessage: message,
      );
      return null;
    }
  }
}
