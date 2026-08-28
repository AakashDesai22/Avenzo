import 'package:equatable/equatable.dart';

class CategoryWasteBreakdownModel extends Equatable {
  final String categoryName;
  final double discardedQuantity;
  final double percentageOfTotalWaste;

  const CategoryWasteBreakdownModel({
    required this.categoryName,
    required this.discardedQuantity,
    required this.percentageOfTotalWaste,
  });

  factory CategoryWasteBreakdownModel.fromJson(Map<String, dynamic> json) {
    return CategoryWasteBreakdownModel(
      categoryName: json['category_name'] as String? ?? 'General',
      discardedQuantity: (json['discarded_quantity'] is num)
          ? (json['discarded_quantity'] as num).toDouble()
          : double.tryParse(json['discarded_quantity'].toString()) ?? 0.0,
      percentageOfTotalWaste: (json['percentage_of_total_waste'] is num)
          ? (json['percentage_of_total_waste'] as num).toDouble()
          : double.tryParse(json['percentage_of_total_waste'].toString()) ?? 0.0,
    );
  }

  @override
  List<Object?> get props => [categoryName, discardedQuantity, percentageOfTotalWaste];
}

class ConsumerWasteMetricsModel extends Equatable {
  final String userId;
  final int totalItemsTracked;
  final int totalItemsConsumed;
  final int totalItemsDiscarded;
  final int totalItemsExpired;
  final double consumedQuantity;
  final double discardedQuantity;
  final double expiredQuantity;
  final double consumptionRatio;
  final double wasteRatio;
  final int? wasteReductionScore;
  final double estimatedMoneySaved;
  final bool hasSufficientHistory;
  final String historyStatus;
  final List<CategoryWasteBreakdownModel> topWastedCategories;

  const ConsumerWasteMetricsModel({
    required this.userId,
    required this.totalItemsTracked,
    required this.totalItemsConsumed,
    required this.totalItemsDiscarded,
    required this.totalItemsExpired,
    required this.consumedQuantity,
    required this.discardedQuantity,
    required this.expiredQuantity,
    required this.consumptionRatio,
    required this.wasteRatio,
    this.wasteReductionScore,
    required this.estimatedMoneySaved,
    required this.hasSufficientHistory,
    required this.historyStatus,
    required this.topWastedCategories,
  });

  factory ConsumerWasteMetricsModel.fromJson(Map<String, dynamic> json) {
    return ConsumerWasteMetricsModel(
      userId: json['user_id'] as String? ?? '',
      totalItemsTracked: json['total_items_tracked'] as int? ?? 0,
      totalItemsConsumed: json['total_items_consumed'] as int? ?? 0,
      totalItemsDiscarded: json['total_items_discarded'] as int? ?? 0,
      totalItemsExpired: json['total_items_expired'] as int? ?? 0,
      consumedQuantity: (json['consumed_quantity'] is num)
          ? (json['consumed_quantity'] as num).toDouble()
          : 0.0,
      discardedQuantity: (json['discarded_quantity'] is num)
          ? (json['discarded_quantity'] as num).toDouble()
          : 0.0,
      expiredQuantity: (json['expired_quantity'] is num)
          ? (json['expired_quantity'] as num).toDouble()
          : 0.0,
      consumptionRatio: (json['consumption_ratio'] is num)
          ? (json['consumption_ratio'] as num).toDouble()
          : 0.0,
      wasteRatio: (json['waste_ratio'] is num)
          ? (json['waste_ratio'] as num).toDouble()
          : 0.0,
      wasteReductionScore: json['waste_reduction_score'] as int?,
      estimatedMoneySaved: (json['estimated_money_saved'] is num)
          ? (json['estimated_money_saved'] as num).toDouble()
          : 0.0,
      hasSufficientHistory: json['has_sufficient_history'] as bool? ?? false,
      historyStatus: json['history_status'] as String? ?? 'No activity logged yet',
      topWastedCategories: (json['top_wasted_categories'] as List<dynamic>?)
              ?.map((e) => CategoryWasteBreakdownModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  @override
  List<Object?> get props => [
        userId,
        totalItemsTracked,
        totalItemsConsumed,
        totalItemsDiscarded,
        totalItemsExpired,
        consumedQuantity,
        discardedQuantity,
        expiredQuantity,
        consumptionRatio,
        wasteRatio,
        wasteReductionScore,
        estimatedMoneySaved,
        hasSufficientHistory,
        historyStatus,
        topWastedCategories,
      ];
}
