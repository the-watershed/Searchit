package com.jureka.historicalmarkers.data

import androidx.lifecycle.LiveData
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update

/**
 * MarkerDao — Room Data Access Object for the [Marker] entity.
 *
 * Provides all database operations needed by the app:
 *  - Bulk seed insert (ignores duplicates via IGNORE conflict strategy).
 *  - Reactive [LiveData] queries for the list and detail screens.
 *  - Single-row update for toggling the visited flag.
 *
 * All suspend functions must be called from a coroutine or another suspend context.
 *
 * Example (inside a coroutine):
 *   val dao = db.markerDao()
 *   val unvisited = dao.getAllMarkers().value?.filter { !it.visited }
 */
@Dao
interface MarkerDao {

    /**
     * Insert a batch of markers.  Uses IGNORE so re-seeding on app launch is safe —
     * existing rows (matched by primary key) are left untouched.
     */
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertAll(markers: List<Marker>)

    /**
     * Return all markers ordered alphabetically by title.
     * Emits a new list every time any row changes (Room LiveData magic).
     */
    @Query("SELECT * FROM markers ORDER BY title ASC")
    fun getAllMarkers(): LiveData<List<Marker>>

    /**
     * Return only the markers the user has already visited, newest visit first.
     */
    @Query("SELECT * FROM markers WHERE visited = 1 ORDER BY visitedAt DESC")
    fun getVisitedMarkers(): LiveData<List<Marker>>

    /**
     * Return only the markers the user has NOT yet visited.
     */
    @Query("SELECT * FROM markers WHERE visited = 0 ORDER BY title ASC")
    fun getUnvisitedMarkers(): LiveData<List<Marker>>

    /**
     * Fetch a single marker by its primary key for the detail screen.
     */
    @Query("SELECT * FROM markers WHERE id = :id LIMIT 1")
    fun getMarkerById(id: Long): LiveData<Marker?>

    /**
     * Persist a full [Marker] row update (used after toggling visited / visitedAt).
     */
    @Update
    suspend fun update(marker: Marker)

    /**
     * Count markers that share a given [markerId] string.
     * Used by [DataSeeder] to detect whether a seed entry already exists.
     */
    @Query("SELECT COUNT(*) FROM markers WHERE markerId = :markerId")
    suspend fun countByMarkerId(markerId: String): Int
}
