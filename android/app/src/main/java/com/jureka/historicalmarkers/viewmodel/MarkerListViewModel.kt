package com.jureka.historicalmarkers.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MediatorLiveData
import androidx.lifecycle.viewModelScope
import com.jureka.historicalmarkers.data.DataSeeder
import com.jureka.historicalmarkers.data.Marker
import com.jureka.historicalmarkers.data.MarkerDatabase
import com.jureka.historicalmarkers.data.MarkerRepository
import kotlinx.coroutines.launch

/**
 * MarkerListViewModel — ViewModel for [MainActivity].
 *
 * Owns the [MarkerRepository] instance and exposes:
 *  - [displayedMarkers]  — the list currently shown (all / visited / unvisited).
 *  - [filterMode]        — the active filter (ALL / VISITED / UNVISITED).
 *
 * On first creation it seeds the database with [DataSeeder.getDefaultMarkers]
 * (safe to call every launch — duplicates are silently ignored by Room).
 *
 * Example:
 *   val vm: MarkerListViewModel by viewModels()
 *   vm.displayedMarkers.observe(this) { list -> adapter.submitList(list) }
 */
class MarkerListViewModel(application: Application) : AndroidViewModel(application) {

    /** Possible filter states for the marker list. */
    enum class FilterMode { ALL, VISITED, UNVISITED }

    private val repo: MarkerRepository

    /** All markers — underlying source for ALL filter mode. */
    private val allMarkers: LiveData<List<Marker>>

    /** Visited markers — source for VISITED filter mode. */
    private val visitedMarkers: LiveData<List<Marker>>

    /** Unvisited markers — source for UNVISITED filter mode. */
    private val unvisitedMarkers: LiveData<List<Marker>>

    /**
     * The list displayed in the RecyclerView.
     * Switches its source when [setFilter] is called.
     */
    val displayedMarkers: MediatorLiveData<List<Marker>> = MediatorLiveData()

    /** Currently active filter; read by the UI to update tab/chip state. */
    var filterMode: FilterMode = FilterMode.ALL
        private set

    init {
        val dao = MarkerDatabase.getInstance(application).markerDao()
        repo = MarkerRepository(dao)

        allMarkers = repo.allMarkers
        visitedMarkers = repo.visitedMarkers
        unvisitedMarkers = repo.unvisitedMarkers

        // Wire up the MediatorLiveData to the ALL source by default
        displayedMarkers.addSource(allMarkers) { list ->
            if (filterMode == FilterMode.ALL) displayedMarkers.value = list
        }
        displayedMarkers.addSource(visitedMarkers) { list ->
            if (filterMode == FilterMode.VISITED) displayedMarkers.value = list
        }
        displayedMarkers.addSource(unvisitedMarkers) { list ->
            if (filterMode == FilterMode.UNVISITED) displayedMarkers.value = list
        }

        // Seed default markers on first launch (idempotent)
        viewModelScope.launch {
            repo.seedMarkers(DataSeeder.getDefaultMarkers())
        }
    }

    /**
     * Switch the displayed list to the given [mode].
     * The MediatorLiveData will immediately re-emit the cached value for that source.
     */
    fun setFilter(mode: FilterMode) {
        filterMode = mode
        // Force re-emission from the now-active source
        displayedMarkers.value = when (mode) {
            FilterMode.ALL -> allMarkers.value ?: emptyList()
            FilterMode.VISITED -> visitedMarkers.value ?: emptyList()
            FilterMode.UNVISITED -> unvisitedMarkers.value ?: emptyList()
        }
    }

    /**
     * Toggle the visited state of [marker].
     * If currently unvisited → records a visit with the current timestamp.
     * If currently visited   → clears the visit record.
     */
    fun toggleVisited(marker: Marker) {
        viewModelScope.launch {
            repo.setVisited(marker, !marker.visited)
        }
    }
}
