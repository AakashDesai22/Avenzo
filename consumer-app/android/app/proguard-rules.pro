# ProGuard / R8 keep rules for ML Kit Text Recognition
-dontwarn com.google.mlkit.vision.text.**
-keep class com.google.mlkit.vision.text.** { *; }

-dontwarn com.google.android.gms.**
-keep class com.google.android.gms.** { *; }
