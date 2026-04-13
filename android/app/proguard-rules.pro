# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified in
# Android SDK/tools/proguard/proguard-android.txt

# Room — keep entity and DAO class names so kapt-generated code works at runtime
-keep class com.jureka.historicalmarkers.data.** { *; }

# Keep Kotlin metadata for reflection used by Room and Lifecycle
-keepattributes *Annotation*, Signature, InnerClasses, EnclosingMethod
