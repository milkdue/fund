package com.leaf.fundpredictor.domain.repository

import com.leaf.fundpredictor.domain.model.Explain
import com.leaf.fundpredictor.domain.model.Fund
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.domain.model.Quote
import com.leaf.fundpredictor.domain.model.WatchlistItem

interface FundRepository {
    suspend fun searchFunds(query: String): List<Fund>
    suspend fun hotFunds(): List<Fund>
    suspend fun getQuote(code: String): Quote
    suspend fun getPrediction(code: String, horizon: String): Prediction
    suspend fun getExplain(code: String, horizon: String): Explain
    suspend fun getKline(code: String, days: Int = 60): List<KlineCandle>
    suspend fun getWatchlist(): List<WatchlistItem>
    suspend fun addWatchlist(code: String): WatchlistItem
}
