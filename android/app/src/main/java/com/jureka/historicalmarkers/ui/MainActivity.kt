package com.jureka.historicalmarkers.ui

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.DividerItemDecoration
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.chip.Chip
import com.jureka.historicalmarkers.R
import com.jureka.historicalmarkers.databinding.ActivityMainBinding
import com.jureka.historicalmarkers.viewmodel.MarkerListViewModel

/**
 * MainActivity — the entry point of the Historical Markers Tracker.
 *
 * Displays a filterable [RecyclerView] of all known historical markers.
 * Three filter chips (All / Visited / Unvisited) narrow the list.
 * Tapping a row opens [MarkerDetailActivity] for the full description and visit toggle.
 * Long-pressing a row toggles its visited state inline for quick check-in.
 *
 * Architecture: observes [MarkerListViewModel.displayedMarkers] (LiveData) and submits
 * the new list to [MarkerAdapter] whenever it changes — zero manual list management.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val viewModel: MarkerListViewModel by viewModels()
    private lateinit var adapter: MarkerAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setSupportActionBar(binding.toolbar)

        setupRecyclerView()
        setupFilterChips()
        observeMarkers()
    }

    // ─── RecyclerView ────────────────────────────────────────────────────────

    private fun setupRecyclerView() {
        adapter = MarkerAdapter(
            onItemClick = { marker ->
                // Open detail screen, passing the marker's primary key
                val intent = Intent(this, MarkerDetailActivity::class.java).apply {
                    putExtra(MarkerDetailActivity.EXTRA_MARKER_ID, marker.id)
                }
                startActivity(intent)
            },
            onItemLongClick = { marker ->
                // Quick toggle via long press — no need to open detail
                viewModel.toggleVisited(marker)
                true
            }
        )

        binding.recyclerView.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = this@MainActivity.adapter
            addItemDecoration(DividerItemDecoration(context, DividerItemDecoration.VERTICAL))
            setHasFixedSize(true)
        }
    }

    // ─── Filter chips ────────────────────────────────────────────────────────

    private fun setupFilterChips() {
        // Map each Chip view to its FilterMode constant
        val chipAll: Chip = binding.chipAll
        val chipVisited: Chip = binding.chipVisited
        val chipUnvisited: Chip = binding.chipUnvisited

        chipAll.setOnClickListener {
            viewModel.setFilter(MarkerListViewModel.FilterMode.ALL)
        }
        chipVisited.setOnClickListener {
            viewModel.setFilter(MarkerListViewModel.FilterMode.VISITED)
        }
        chipUnvisited.setOnClickListener {
            viewModel.setFilter(MarkerListViewModel.FilterMode.UNVISITED)
        }
    }

    // ─── LiveData observation ────────────────────────────────────────────────

    private fun observeMarkers() {
        viewModel.displayedMarkers.observe(this) { markers ->
            adapter.submitList(markers)

            // Show empty-state message when the filtered list is empty
            if (markers.isNullOrEmpty()) {
                binding.textEmpty.text = when (viewModel.filterMode) {
                    MarkerListViewModel.FilterMode.VISITED ->
                        getString(R.string.empty_visited)
                    MarkerListViewModel.FilterMode.UNVISITED ->
                        getString(R.string.empty_unvisited)
                    else -> getString(R.string.empty_all)
                }
                binding.textEmpty.visibility = android.view.View.VISIBLE
                binding.recyclerView.visibility = android.view.View.GONE
            } else {
                binding.textEmpty.visibility = android.view.View.GONE
                binding.recyclerView.visibility = android.view.View.VISIBLE
            }
        }
    }

    // ─── Options menu ─────────────────────────────────────────────────────────

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean = when (item.itemId) {
        R.id.action_filter_all -> {
            viewModel.setFilter(MarkerListViewModel.FilterMode.ALL)
            binding.chipAll.isChecked = true
            true
        }
        R.id.action_filter_visited -> {
            viewModel.setFilter(MarkerListViewModel.FilterMode.VISITED)
            binding.chipVisited.isChecked = true
            true
        }
        R.id.action_filter_unvisited -> {
            viewModel.setFilter(MarkerListViewModel.FilterMode.UNVISITED)
            binding.chipUnvisited.isChecked = true
            true
        }
        else -> super.onOptionsItemSelected(item)
    }
}
