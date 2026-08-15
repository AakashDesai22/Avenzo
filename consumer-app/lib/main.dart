import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/app.dart';

/// AVENZO Consumer App — Entry Point
///
/// State management: Riverpod (flutter_riverpod)
/// Navigation: go_router
///
/// NOTE: This is a foundation scaffold.
/// Full UI implementation begins in Phase 3.
void main() {
  // Ensure Flutter bindings are initialized
  WidgetsFlutterBinding.ensureInitialized();

  // TODO (Phase 3): Initialize Firebase
  // await Firebase.initializeApp();

  // TODO (Phase 3): Initialize FCM
  // await FirebaseMessaging.instance.requestPermission();

  // Wrap app in ProviderScope for Riverpod
  runApp(
    const ProviderScope(
      child: AvenzoApp(),
    ),
  );
}
