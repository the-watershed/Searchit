/*
 * Root build.gradle.kts — Historical Markers Tracker
 * Declares plugin versions shared across all sub-modules.
 */

plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.kapt) apply false
}
