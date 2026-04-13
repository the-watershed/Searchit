package com.jureka.historicalmarkers.data

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Marker — Room entity representing a single historical marker.
 *
 * Each marker is a real-world sign or monument commemorating a person, event, or place.
 * The [visited] flag records whether the user has checked in at this location.
 * [visitedAt] stores the Unix epoch milliseconds of the most recent visit, or null if never visited.
 *
 * Fields:
 *  - id:          Auto-generated primary key (assigned by Room on first insert).
 *  - markerId:    Stable string identifier (e.g. "VA-0042") used for seeding and deduplication.
 *  - title:       Short name of the marker (e.g. "Battle of Cedar Creek").
 *  - description: Longer historical description text displayed in the detail screen.
 *  - city:        City or nearest town where the marker stands.
 *  - state:       US state abbreviation.
 *  - latitude:    GPS latitude of the marker's location.
 *  - longitude:   GPS longitude of the marker's location.
 *  - visited:     True once the user has marked it as visited.
 *  - visitedAt:   Timestamp (epoch ms) of most recent check-in, null if never visited.
 *
 * Example:
 *   val marker = Marker(
 *       markerId = "PA-0001",
 *       title    = "Liberty Bell",
 *       description = "Originally hung in the Pennsylvania State House…",
 *       city = "Philadelphia", state = "PA",
 *       latitude = 39.9496, longitude = -75.1503
 *   )
 */
@Entity(tableName = "markers")
data class Marker(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    /** Stable external identifier, e.g. "PA-0001". Used for seed deduplication. */
    val markerId: String,

    val title: String,
    val description: String,
    val city: String,
    val state: String,
    val latitude: Double,
    val longitude: Double,

    /** Whether the user has visited this marker. */
    val visited: Boolean = false,

    /** Unix epoch milliseconds of the last check-in; null if never visited. */
    val visitedAt: Long? = null
)
