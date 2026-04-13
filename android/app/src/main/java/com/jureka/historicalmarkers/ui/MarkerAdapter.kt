package com.jureka.historicalmarkers.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.jureka.historicalmarkers.R
import com.jureka.historicalmarkers.data.Marker
import com.jureka.historicalmarkers.databinding.ItemMarkerBinding
import java.text.DateFormat
import java.util.Date

/**
 * MarkerAdapter — [ListAdapter] that backs the [RecyclerView] in [MainActivity].
 *
 * Uses [DiffUtil] via [ListAdapter] for efficient, animated list updates — only changed rows
 * are redrawn when the LiveData emits a new list after a visit toggle.
 *
 * Each row shows:
 *  - Marker title
 *  - City, State
 *  - A ✔ badge and "Visited on …" line when [Marker.visited] is true
 *
 * Interactions:
 *  - Single tap  → [onItemClick]  (opens detail screen)
 *  - Long press  → [onItemLongClick]  (quick toggle, returns true to consume the event)
 *
 * @param onItemClick      Called with the tapped [Marker].
 * @param onItemLongClick  Called with the long-pressed [Marker]; must return true.
 */
class MarkerAdapter(
    private val onItemClick: (Marker) -> Unit,
    private val onItemLongClick: (Marker) -> Boolean
) : ListAdapter<Marker, MarkerAdapter.MarkerViewHolder>(DIFF_CALLBACK) {

    // ─── ViewHolder ───────────────────────────────────────────────────────────

    inner class MarkerViewHolder(private val binding: ItemMarkerBinding) :
        RecyclerView.ViewHolder(binding.root) {

        /**
         * Bind a [Marker] to the row views.
         * The visited badge row is shown/hidden based on [Marker.visited].
         */
        fun bind(marker: Marker) {
            binding.textMarkerTitle.text = marker.title
            binding.textMarkerLocation.text =
                itemView.context.getString(R.string.location_format, marker.city, marker.state)

            if (marker.visited) {
                binding.imageVisitedBadge.setImageResource(R.drawable.ic_check_circle)
                binding.textVisitedDate.text = marker.visitedAt?.let {
                    DateFormat.getDateInstance(DateFormat.SHORT).format(Date(it))
                } ?: itemView.context.getString(R.string.visited_label)
                binding.layoutVisitedBadge.visibility = android.view.View.VISIBLE
            } else {
                binding.imageVisitedBadge.setImageResource(R.drawable.ic_add_location)
                binding.layoutVisitedBadge.visibility = android.view.View.GONE
            }

            binding.root.setOnClickListener { onItemClick(marker) }
            binding.root.setOnLongClickListener { onItemLongClick(marker) }
        }
    }

    // ─── Adapter overrides ────────────────────────────────────────────────────

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MarkerViewHolder {
        val binding = ItemMarkerBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return MarkerViewHolder(binding)
    }

    override fun onBindViewHolder(holder: MarkerViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    // ─── DiffUtil ─────────────────────────────────────────────────────────────

    companion object {
        /**
         * [DiffUtil.ItemCallback] compares markers by their stable primary key for identity
         * and full field equality for content — ensures only the exact changed row is redrawn.
         */
        private val DIFF_CALLBACK = object : DiffUtil.ItemCallback<Marker>() {
            override fun areItemsTheSame(old: Marker, new: Marker): Boolean = old.id == new.id
            override fun areContentsTheSame(old: Marker, new: Marker): Boolean = old == new
        }
    }
}
