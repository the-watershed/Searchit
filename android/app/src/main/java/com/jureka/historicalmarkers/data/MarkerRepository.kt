package com.jureka.historicalmarkers.data

import androidx.lifecycle.LiveData

/**
 * MarkerRepository — mediates between the ViewModel layer and the Room DAO.
 *
 * Keeps the ViewModel ignorant of the database implementation details.
 * All coroutine-based writes are performed here; LiveData queries are passed through directly
 * since Room already handles threading for LiveData observation.
 *
 * @param dao The [MarkerDao] instance injected from the database singleton.
 *
 * Example:
 *   val repo = MarkerRepository(MarkerDatabase.getInstance(ctx).markerDao())
 *   repo.allMarkers.observe(owner) { markers -> adapter.submitList(markers) }
 */
class MarkerRepository(private val dao: MarkerDao) {

    /** All markers sorted A→Z by title; updates reactively whenever the DB changes. */
    val allMarkers: LiveData<List<Marker>> = dao.getAllMarkers()

    /** Subset of visited markers, newest first. */
    val visitedMarkers: LiveData<List<Marker>> = dao.getVisitedMarkers()

    /** Subset of not-yet-visited markers, A→Z. */
    val unvisitedMarkers: LiveData<List<Marker>> = dao.getUnvisitedMarkers()

    /**
     * Observe a single marker by its primary key.
     * Used by [MarkerDetailActivity] to reactively track visit state changes.
     */
    fun getMarkerById(id: Long): LiveData<Marker?> = dao.getMarkerById(id)

    /**
     * Mark the given marker as visited right now, or un-mark it.
     *
     * @param marker  The marker to update.
     * @param visited Pass `true` to record a visit, `false` to clear it.
     */
    suspend fun setVisited(marker: Marker, visited: Boolean) {
        val updated = marker.copy(
            visited = visited,
            visitedAt = if (visited) System.currentTimeMillis() else null
        )
        dao.update(updated)
    }

    /**
     * Seed the database with the provided list of markers.
     * Safe to call on every app launch — existing rows are ignored via IGNORE conflict strategy.
     */
    suspend fun seedMarkers(markers: List<Marker>) {
        dao.insertAll(markers)
    }
}
