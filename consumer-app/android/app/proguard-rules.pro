# =============================================================================
# AVENZO — R8 / ProGuard rules
# Google ML Kit Text Recognition
# =============================================================================

# Keep ML Kit core/common classes required during automatic initialization.
-keep class com.google.mlkit.common.** { *; }

# Keep ML Kit text-recognition implementation and internal classes.
-keep class com.google.mlkit.vision.text.** { *; }

# Keep ML Kit component/provider metadata and dependency injection classes.
-keep class com.google.mlkit.** { *; }

# ML Kit may reference classes that are supplied dynamically.
-dontwarn com.google.mlkit.**

# Google Play Services dependencies used by ML Kit.
-keep class com.google.android.gms.common.** { *; }
-keep class com.google.android.gms.tasks.** { *; }
-dontwarn com.google.android.gms.**