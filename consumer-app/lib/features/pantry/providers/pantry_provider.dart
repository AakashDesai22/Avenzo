import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/services/expiry_notification_scheduler.dart';
import '../../../shared/models/pantry_item_model.dart';
import '../data/pantry_repository.dart';

abstract class PantryState extends Equatable {
  const PantryState();

  @override
  List<Object?> get props => [];
}

class PantryInitial extends PantryState {}

class PantryLoading extends PantryState {}

class PantryLoaded extends PantryState {
  final List<PantryItemModel> items;
  final String? activeFilter; // null = All, 'pantry', 'fridge', 'freezer'

  const PantryLoaded({
    required this.items,
    this.activeFilter,
  });

  PantryLoaded copyWith({
    List<PantryItemModel>? items,
    String? activeFilter,
  }) {
    return PantryLoaded(
      items: items ?? this.items,
      activeFilter: activeFilter != null ? (activeFilter == 'all' ? null : activeFilter) : this.activeFilter,
    );
  }

  @override
  List<Object?> get props => [items, activeFilter];
}

class PantryError extends PantryState {
  final String message;

  const PantryError(this.message);

  @override
  List<Object?> get props => [message];
}

final pantryRepositoryProvider = Provider<PantryRepository>((ref) {
  return PantryRepository();
});

final expiryNotificationSchedulerProvider = Provider<ExpiryNotificationScheduler>((ref) {
  return ExpiryNotificationScheduler();
});

final pantryNotifierProvider =
    StateNotifierProvider<PantryNotifier, PantryState>((ref) {
  return PantryNotifier(
    repository: ref.watch(pantryRepositoryProvider),
    scheduler: ref.watch(expiryNotificationSchedulerProvider),
  );
});

final expiringPantryItemsProvider =
    FutureProvider<List<PantryItemModel>>((ref) async {
  final repo = ref.watch(pantryRepositoryProvider);
  return repo.getExpiringItems();
});

class PantryNotifier extends StateNotifier<PantryState> {
  final PantryRepository _repository;
  final ExpiryNotificationScheduler? _scheduler;

  PantryNotifier({
    required PantryRepository repository,
    ExpiryNotificationScheduler? scheduler,
  })  : _repository = repository,
        _scheduler = scheduler,
        super(PantryInitial());

  Future<void> _syncNotifications(List<PantryItemModel> items) async {
    if (_scheduler != null) {
      await _scheduler.syncExpiryNotifications(items);
    }
  }

  Future<void> fetchPantryItems({String? storageLocation}) async {
    state = PantryLoading();
    try {
      final filter = (storageLocation == 'all') ? null : storageLocation;
      final items = await _repository.getPantryItems(storageLocation: filter);
      state = PantryLoaded(items: items, activeFilter: filter);
      await _syncNotifications(items);
    } catch (e) {
      final msg = e is ApiException ? e.message : 'Failed to load pantry items.';
      state = PantryError(msg);
    }
  }

  Future<void> setFilter(String? storageLocation) async {
    await fetchPantryItems(storageLocation: storageLocation);
  }

  Future<bool> addItem({
    String? productId,
    String? batchId,
    String? customName,
    String? barcode,
    required double quantity,
    required String unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    required String storageLocation,
    String? notes,
  }) async {
    try {
      final newItem = await _repository.addPantryItem(
        productId: productId,
        batchId: batchId,
        customName: customName,
        barcode: barcode,
        quantity: quantity,
        unit: unit,
        purchaseDate: purchaseDate,
        expiryDate: expiryDate,
        storageLocation: storageLocation,
        notes: notes,
      );

      if (state is PantryLoaded) {
        final current = (state as PantryLoaded);
        final newItems = [newItem, ...current.items];
        state = PantryLoaded(
          items: newItems,
          activeFilter: current.activeFilter,
        );
        await _syncNotifications(newItems);
      } else {
        await fetchPantryItems();
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<bool> updateItem({
    required String id,
    String? customName,
    double? quantity,
    String? unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    String? storageLocation,
    String? notes,
  }) async {
    try {
      final updated = await _repository.updatePantryItem(
        id: id,
        customName: customName,
        quantity: quantity,
        unit: unit,
        purchaseDate: purchaseDate,
        expiryDate: expiryDate,
        storageLocation: storageLocation,
        notes: notes,
      );

      if (state is PantryLoaded) {
        final current = (state as PantryLoaded);
        final newItems = current.items.map((i) => i.id == id ? updated : i).toList();
        state = PantryLoaded(
          items: newItems,
          activeFilter: current.activeFilter,
        );
        await _syncNotifications(newItems);
      } else {
        await fetchPantryItems();
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<bool> consumeItem(String id, double quantity) async {
    try {
      final updated = await _repository.consumeItem(id, quantity);
      if (state is PantryLoaded) {
        final current = (state as PantryLoaded);
        List<PantryItemModel> newItems;
        if (updated.status == 'consumed' || updated.quantity <= 0) {
          newItems = current.items.where((i) => i.id != id).toList();
          if (_scheduler != null) {
            await _scheduler.cancelItemNotifications(id);
          }
        } else {
          newItems = current.items.map((i) => i.id == id ? updated : i).toList();
          await _syncNotifications(newItems);
        }
        state = PantryLoaded(
          items: newItems,
          activeFilter: current.activeFilter,
        );
      } else {
        await fetchPantryItems();
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<bool> discardItem(String id, double quantity) async {
    try {
      final updated = await _repository.discardItem(id, quantity);
      if (state is PantryLoaded) {
        final current = (state as PantryLoaded);
        List<PantryItemModel> newItems;
        if (updated.status == 'discarded' || updated.quantity <= 0) {
          newItems = current.items.where((i) => i.id != id).toList();
          if (_scheduler != null) {
            await _scheduler.cancelItemNotifications(id);
          }
        } else {
          newItems = current.items.map((i) => i.id == id ? updated : i).toList();
          await _syncNotifications(newItems);
        }
        state = PantryLoaded(
          items: newItems,
          activeFilter: current.activeFilter,
        );
      } else {
        await fetchPantryItems();
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<bool> deleteItem(String id) async {
    try {
      await _repository.deletePantryItem(id);
      if (_scheduler != null) {
        await _scheduler.cancelItemNotifications(id);
      }
      if (state is PantryLoaded) {
        final current = (state as PantryLoaded);
        final newItems = current.items.where((i) => i.id != id).toList();
        state = PantryLoaded(
          items: newItems,
          activeFilter: current.activeFilter,
        );
      } else {
        await fetchPantryItems();
      }
      return true;
    } catch (e) {
      return false;
    }
  }
}
