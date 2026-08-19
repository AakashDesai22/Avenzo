import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'app/app.dart';
import 'core/services/fcm_service.dart';
import 'firebase_options.dart';

/// AVENZO Consumer App — Entry Point
///
/// State management: Riverpod (flutter_riverpod)
/// Navigation: go_router
/// Push Notifications: Firebase Cloud Messaging (FCM) & Local Notifications
Future<void> main() async {
  // Ensure Flutter bindings are initialized
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase App instance
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  // Register top-level FCM background message handler
  FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

  // Wrap app in ProviderScope for Riverpod state management
  runApp(
    const ProviderScope(
      child: AvenzoApp(),
    ),
  );
}
