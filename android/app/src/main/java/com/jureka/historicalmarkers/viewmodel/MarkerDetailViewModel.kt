package com.jureka.historicalmarkers.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.viewModelScope
import com.jureka.historicalmarkers.data.Marker
import com.jureka.historicalmarkers.data.MarkerDatabase
import com.jureka.historicalmarkers.data.MarkerRepository
import kotlinx.coroutines.launch

/**
 * MarkerDetailViewModel — ViewModel for [MarkerDetailActivity].
 *
 * Exposes a single [marker] LiveData that reactively tracks the DB state for one marker.
 * Provides [toggleVisited] so the detail screen can check/uncheck a visit.
 *
 * @param application  Application context (required by AndroidViewModel).
 *
 * Usage:
 *   val vm: MarkerDetailViewModel by viewModels()
 *   vm.loadMarker(markerId)
 *   vm.marker.observe(this) { m -> if (m != null) bindUi(m) }
 */
class MarkerDetailViewModel(application: Application) : AndroidViewModel(application) {

    private val repo: MarkerRepository = MarkerRepository(
        MarkerDatabase.getInstance(application).markerDao()
    )

    /**
     * LiveData for the currently loaded marker.
     * Updated reactively whenever the DB row changes (e.g. after toggleVisited).
     */
    var marker: LiveData<Marker?>? = null
        private set

    /**
     * Begin observing the marker with the given primary key [id].
     * Call this once from [MarkerDetailActivity.onCreate] after extracting the ID from the intent.
     */
    fun loadMarker(id: Long) {
        marker = repo.getMarkerById(id)
    }

    /**
     * Toggle the visited state of the currently held [marker] value.
     * Silently does nothing if the marker has not been loaded yet.
     */
    fun toggleVisited() {
        val current = marker?.value ?: return
        viewModelScope.launch {
            repo.setVisited(current, !current.visited)
        }
    }
}
