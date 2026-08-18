import 'package:flutter/material.dart';

/// AVENZO Consumer App — Color System
/// Clean, fresh, approachable, waste-conscious aesthetic.
class AppColors {
  AppColors._();

  // Primary Palette — Fresh Emerald & Teal
  static const Color primary = Color(0xFF0D9488);        // Teal 600
  static const Color primaryDark = Color(0xFF0F766E);    // Teal 700
  static const Color primaryLight = Color(0xFFCCFBF1);   // Teal 100

  // Secondary Palette — Mint Accent
  static const Color secondary = Color(0xFF10B981);      // Emerald 500
  static const Color secondaryLight = Color(0xFFD1FAE5);  // Emerald 100

  // Neutral Palette
  static const Color background = Color(0xFFF8FAFC);     // Slate 50
  static const Color surface = Color(0xFFFFFFFF);        // White
  static const Color surfaceVariant = Color(0xFFF1F5F9); // Slate 100
  static const Color textPrimary = Color(0xFF0F172A);    // Slate 900
  static const Color textSecondary = Color(0xFF475569);  // Slate 600
  static const Color textMuted = Color(0xFF94A3B8);      // Slate 400
  static const Color border = Color(0xFFE2E8F0);         // Slate 200

  // Status & Expiry Risk Indicators
  static const Color safe = Color(0xFF10B981);           // Green (Safe)
  static const Color warning = Color(0xFFF59E0B);        // Amber (Expiring Soon - 7d)
  static const Color critical = Color(0xFFEF4444);       // Red (Critical - 3d/Expired)
  static const Color info = Color(0xFF3B82F6);           // Blue (Info)

  // Dark Theme Accents
  static const Color darkBackground = Color(0xFF0F172A); // Slate 900
  static const Color darkSurface = Color(0xFF1E293B);    // Slate 800
  static const Color darkSurfaceVariant = Color(0xFF334155); // Slate 700
}
