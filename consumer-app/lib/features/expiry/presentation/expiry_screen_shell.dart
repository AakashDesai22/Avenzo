import 'package:flutter/material.dart';
import '../../../app/theme/app_colors.dart';

/// Foundation Screen for Expiry Tracking
/// (Personal consumer expiry tracking depends on backend Consumer Pantry module)
class ExpiryScreenShell extends StatelessWidget {
  const ExpiryScreenShell({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Expiring Soon'),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: AppColors.warning.withOpacity(0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.timer_rounded,
                  size: 64,
                  color: AppColors.warning,
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Personal Expiry Tracking',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Personalized expiry tracking and waste reduction alerts will become active once your Consumer Digital Pantry is connected to the backend.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 24),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      const Icon(Icons.notifications_active_outlined, color: AppColors.primary),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'Smart alerts notify you 7 days and 3 days before items expire.',
                          style: TextStyle(fontSize: 13, color: AppColors.textPrimary),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
