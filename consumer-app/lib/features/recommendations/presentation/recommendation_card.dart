import 'package:flutter/material.dart';
import '../data/recommendation_models.dart';

class RecommendationCard extends StatelessWidget {
  final RecommendationModel recommendation;
  final VoidCallback onDismiss;
  final VoidCallback? onActionTap;

  const RecommendationCard({
    super.key,
    required this.recommendation,
    required this.onDismiss,
    this.onActionTap,
  });

  Color _getPriorityColor(String priority) {
    switch (priority.toUpperCase()) {
      case 'CRITICAL':
        return Colors.red.shade700;
      case 'HIGH':
        return Colors.orange.shade800;
      case 'MEDIUM':
        return Colors.blue.shade700;
      case 'LOW':
      default:
        return Colors.teal.shade700;
    }
  }

  IconData _getTypeIcon(String type) {
    switch (type.toUpperCase()) {
      case 'USE_SOON':
      case 'EXPIRY_PRIORITY':
        return Icons.timer_outlined;
      case 'WASTE_RISK':
        return Icons.warning_amber_rounded;
      case 'OVERSTOCK':
        return Icons.inventory_2_outlined;
      case 'CONSUMPTION_INSIGHT':
        return Icons.insights_outlined;
      case 'SMART_ACTION':
      default:
        return Icons.lightbulb_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final priorityColor = _getPriorityColor(recommendation.priority);
    final typeIcon = _getTypeIcon(recommendation.recommendationType);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: priorityColor.withAlpha(80), width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header: Icon + Badge + Dismiss Button
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: priorityColor.withAlpha(30),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(typeIcon, color: priorityColor, size: 22),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: priorityColor,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    recommendation.priority.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close, size: 20, color: Colors.grey),
                  onPressed: onDismiss,
                  tooltip: 'Dismiss recommendation',
                ),
              ],
            ),

            const SizedBox(height: 12),

            // Title
            Text(
              recommendation.title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                height: 1.2,
              ),
            ),

            const SizedBox(height: 6),

            // Message
            Text(
              recommendation.message,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade800,
                height: 1.3,
              ),
            ),

            const SizedBox(height: 12),

            // Explainability Reason Container
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline, size: 16, color: Colors.blueGrey.shade700),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Why: ${recommendation.reason}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blueGrey.shade900,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Suggested Action Button
            if (recommendation.suggestedAction != null &&
                recommendation.suggestedAction!.isNotEmpty) ...[
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: onActionTap ?? () {},
                  icon: const Icon(Icons.arrow_forward_rounded, size: 16),
                  label: Text(
                    recommendation.suggestedAction!,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  ),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: priorityColor,
                    side: BorderSide(color: priorityColor.withAlpha(150)),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
