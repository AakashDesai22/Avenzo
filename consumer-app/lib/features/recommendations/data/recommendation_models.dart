import 'package:flutter/foundation.dart';

@immutable
class RecommendationModel {
  final String id;
  final String userId;
  final String? pantryItemId;
  final String recommendationType; // USE_SOON, WASTE_RISK, OVERSTOCK, CONSUMPTION_INSIGHT, EXPIRY_PRIORITY, SMART_ACTION
  final String priority; // CRITICAL, HIGH, MEDIUM, LOW
  final String title;
  final String message;
  final String reason;
  final String? suggestedAction;
  final String? metadataJson;
  final bool isDismissed;
  final DateTime createdAt;

  const RecommendationModel({
    required this.id,
    required this.userId,
    this.pantryItemId,
    required this.recommendationType,
    required this.priority,
    required this.title,
    required this.message,
    required this.reason,
    this.suggestedAction,
    this.metadataJson,
    required this.isDismissed,
    required this.createdAt,
  });

  factory RecommendationModel.fromJson(Map<String, dynamic> json) {
    return RecommendationModel(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      pantryItemId: json['pantry_item_id'] as String?,
      recommendationType: json['recommendation_type'] as String? ?? 'USE_SOON',
      priority: json['priority'] as String? ?? 'MEDIUM',
      title: json['title'] as String? ?? '',
      message: json['message'] as String? ?? '',
      reason: json['reason'] as String? ?? '',
      suggestedAction: json['suggested_action'] as String?,
      metadataJson: json['metadata_json'] as String?,
      isDismissed: json['is_dismissed'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'pantry_item_id': pantryItemId,
      'recommendation_type': recommendationType,
      'priority': priority,
      'title': title,
      'message': message,
      'reason': reason,
      'suggested_action': suggestedAction,
      'metadata_json': metadataJson,
      'is_dismissed': isDismissed,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

@immutable
class RecommendationSummaryModel {
  final int totalActiveItems;
  final int expiring3dCount;
  final int expiring7dCount;
  final int estimatedWasteRiskCount;
  final bool hasSufficientHistory;
  final String historyStatus;

  const RecommendationSummaryModel({
    required this.totalActiveItems,
    required this.expiring3dCount,
    required this.expiring7dCount,
    required this.estimatedWasteRiskCount,
    required this.hasSufficientHistory,
    required this.historyStatus,
  });

  factory RecommendationSummaryModel.fromJson(Map<String, dynamic> json) {
    return RecommendationSummaryModel(
      totalActiveItems: json['total_active_items'] as int? ?? 0,
      expiring3dCount: json['expiring_3d_count'] as int? ?? 0,
      expiring7dCount: json['expiring_7d_count'] as int? ?? 0,
      estimatedWasteRiskCount: json['estimated_waste_risk_count'] as int? ?? 0,
      hasSufficientHistory: json['has_sufficient_history'] as bool? ?? false,
      historyStatus: json['history_status'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total_active_items': totalActiveItems,
      'expiring_3d_count': expiring3dCount,
      'expiring_7d_count': expiring7dCount,
      'estimated_waste_risk_count': estimatedWasteRiskCount,
      'has_sufficient_history': hasSufficientHistory,
      'history_status': historyStatus,
    };
  }
}
