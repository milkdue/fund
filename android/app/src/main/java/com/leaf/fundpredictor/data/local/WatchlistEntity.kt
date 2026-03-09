package com.leaf.fundpredictor.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "watchlist")
data class WatchlistEntity(
    @PrimaryKey val fundCode: String,
    val userId: String,
)
