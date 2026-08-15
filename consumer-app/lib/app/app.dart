import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// AVENZO App Root Widget
///
/// Configures:
/// - Material theme
/// - Navigation (go_router — Phase 3)
/// - Global error handling
///
/// NOTE: This is a placeholder. Full implementation in Phase 3.
class AvenzoApp extends ConsumerWidget {
  const AvenzoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // TODO (Phase 3): Replace with GoRouter navigation
    return MaterialApp(
      title: 'AVENZO',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1A73E8),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1A73E8),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      // Placeholder home screen
      home: Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.inventory_2_outlined,
                size: 64,
                color: Color(0xFF1A73E8),
              ),
              const SizedBox(height: 16),
              const Text(
                'AVENZO',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'One Product. One Lifecycle. One Intelligence.',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 32),
              const Text(
                'Foundation Phase — UI coming in Phase 3',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
