package com.jureka.historicalmarkers.ui

import android.os.Bundle
import android.view.View
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.jureka.historicalmarkers.R
import com.jureka.historicalmarkers.databinding.ActivityMarkerDetailBinding
import com.jureka.historicalmarkers.viewmodel.MarkerDetailViewModel
import java.text.DateFormat
import java.util.Date

/**
 * MarkerDetailActivity — full-detail screen for a single historical marker.
 *
 * Shows the marker title, city/state, a full description, and the visit status.
 * The FAB toggles visited/unvisited and records the current timestamp.
 *
 * Launched by [MainActivity] with [EXTRA_MARKER_ID] in the intent.
 */
class MarkerDetailActivity : AppCompatActivity() {

    companion object {
        /** Intent key for the marker's Room primary key (Long). */
        const val EXTRA_MARKER_ID = "extra_marker_id"
    }

    private lateinit var binding: ActivityMarkerDetailBinding
    private val viewModel: MarkerDetailViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMarkerDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        val markerId = intent.getLongExtra(EXTRA_MARKER_ID, -1L)
        if (markerId == -1L) {
            finish()
            return
        }

        viewModel.loadMarker(markerId)
        observeMarker()

        binding.fabVisited.setOnClickListener {
            viewModel.toggleVisited()
        }
    }

    /**
     * Observe the single-marker LiveData from [MarkerDetailViewModel] and bind it to the UI.
     * Room re-emits after every [toggleVisited] call, so the FAB icon stays in sync.
     */
    private fun observeMarker() {
        viewModel.marker?.observe(this) { marker ->
            if (marker == null) return@observe

            // Toolbar title mirrors the marker title
            supportActionBar?.title = marker.title

            binding.textTitle.text = marker.title
            binding.textLocation.text = getString(R.string.location_format, marker.city, marker.state)
            binding.textDescription.text = marker.description
            binding.textCoords.text = getString(
                R.string.coords_format,
                marker.latitude,
                marker.longitude
            )

            if (marker.visited) {
                binding.fabVisited.setImageResource(R.drawable.ic_check_circle)
                binding.layoutVisitInfo.visibility = View.VISIBLE
                val dateStr = marker.visitedAt?.let {
                    DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT)
                        .format(Date(it))
                } ?: getString(R.string.unknown_date)
                binding.textVisitedAt.text = getString(R.string.visited_on, dateStr)
            } else {
                binding.fabVisited.setImageResource(R.drawable.ic_add_location)
                binding.layoutVisitInfo.visibility = View.GONE
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
