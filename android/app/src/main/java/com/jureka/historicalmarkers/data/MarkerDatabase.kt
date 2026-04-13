package com.jureka.historicalmarkers.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * MarkerDatabase — Room database singleton for the Historical Markers Tracker.
 *
 * Contains a single table: [Marker] (entity).
 * Access the DAO via [markerDao].
 *
 * Uses a double-checked-locking singleton so only one instance exists per process —
 * Room databases are expensive to create and must never be opened on the main thread.
 *
 * Usage:
 *   val db = MarkerDatabase.getInstance(context)
 *   val dao = db.markerDao()
 */
@Database(entities = [Marker::class], version = 1, exportSchema = false)
abstract class MarkerDatabase : RoomDatabase() {

    /** Provides access to all marker CRUD operations. */
    abstract fun markerDao(): MarkerDao

    companion object {
        private const val DATABASE_NAME = "historical_markers.db"

        @Volatile
        private var instance: MarkerDatabase? = null

        /**
         * Return the singleton database instance, creating it if necessary.
         *
         * @param context Application context (never an Activity context — avoids leaks).
         */
        fun getInstance(context: Context): MarkerDatabase =
            instance ?: synchronized(this) {
                instance ?: buildDatabase(context).also { instance = it }
            }

        private fun buildDatabase(context: Context): MarkerDatabase =
            Room.databaseBuilder(
                context.applicationContext,
                MarkerDatabase::class.java,
                DATABASE_NAME
            ).build()
    }
}
