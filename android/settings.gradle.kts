/*
 * settings.gradle.kts — Historical Markers Tracker
 * Defines the root project name and includes the :app module.
 */

pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "HistoricalMarkers"
include(":app")
