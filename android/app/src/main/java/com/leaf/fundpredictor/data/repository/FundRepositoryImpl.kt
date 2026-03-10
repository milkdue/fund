package com.leaf.fundpredictor.data.repository

import com.leaf.fundpredictor.data.local.WatchlistDao
import com.leaf.fundpredictor.data.local.WatchlistEntity
import com.leaf.fundpredictor.data.remote.AlertRuleRequest
import com.leaf.fundpredictor.data.remote.FeedbackRequest
import com.leaf.fundpredictor.data.remote.FundApi
import com.leaf.fundpredictor.data.remote.WatchlistAddRequest
import com.leaf.fundpredictor.domain.model.Explain
import com.leaf.fundpredictor.domain.model.ExplainFactor
import com.leaf.fundpredictor.domain.model.Fund
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.domain.model.Quote
import com.leaf.fundpredictor.domain.model.WatchlistItem
import com.leaf.fundpredictor.domain.repository.FundRepository
import javax.inject.Inject

class FundRepositoryImpl @Inject constructor(
    private val api: FundApi,
    private val watchlistDao: WatchlistDao,
) : FundRepository {

    override suspend fun searchFunds(query: String): List<Fund> {
        return api.searchFunds(query).map { Fund(it.code, it.name, it.category) }
    }

    override suspend fun hotFunds(): List<Fund> {
        return api.hotFunds().map { Fund(it.code, it.name, it.category) }
    }

    override suspend fun getQuote(code: String): Quote {
        val dto = api.getQuote(code)
        return Quote(dto.code, dto.asOf, dto.dataFreshness, dto.nav, dto.dailyChangePct, dto.volatility20d)
    }

    override suspend fun getPrediction(code: String, horizon: String): Prediction {
        val dto = api.getPrediction(code, horizon)
        return Prediction(
            dto.code,
            dto.horizon,
            dto.asOf,
            dto.dataFreshness,
            dto.upProbability,
            dto.expectedReturnPct,
            dto.confidence,
        )
    }

    override suspend fun getExplain(code: String, horizon: String): Explain {
        val dto = api.getExplain(code, horizon)
        val ci = dto.confidenceIntervalPct
        return Explain(
            code = dto.code,
            horizon = dto.horizon,
            dataFreshness = dto.dataFreshness,
            confidenceIntervalPct = Pair(ci.getOrElse(0) { 0.0 }, ci.getOrElse(1) { 0.0 }),
            topFactors = dto.topFactors.map { ExplainFactor(it.name, it.contribution) },
            riskFlags = dto.riskFlags,
        )
    }

    override suspend fun getKline(code: String, days: Int): List<KlineCandle> {
        val dto = api.getKline(code, days)
        return dto.items.map {
            KlineCandle(
                ts = it.ts,
                open = it.open,
                high = it.high,
                low = it.low,
                close = it.close,
            )
        }
    }

    override suspend fun getWatchlist(): List<WatchlistItem> {
        return try {
            val remote = api.getWatchlist()
            watchlistDao.upsert(remote.map { WatchlistEntity(fundCode = it.fundCode, userId = it.userId) })
            remote.map { WatchlistItem(it.userId, it.fundCode) }
        } catch (_: Exception) {
            watchlistDao.getAll().map { WatchlistItem(it.userId, it.fundCode) }
        }
    }

    override suspend fun addWatchlist(code: String): WatchlistItem {
        val remote = api.addWatchlist(WatchlistAddRequest(code))
        watchlistDao.upsert(WatchlistEntity(fundCode = remote.fundCode, userId = remote.userId))
        return WatchlistItem(remote.userId, remote.fundCode)
    }

    override suspend fun submitFeedback(code: String, horizon: String, isHelpful: Boolean, score: Int): Boolean {
        api.postFeedback(
            code = code,
            payload = FeedbackRequest(
                horizon = horizon,
                isHelpful = isHelpful,
                score = score.coerceIn(1, 5),
            ),
        )
        return true
    }

    override suspend fun upsertDefaultAlert(code: String, horizon: String): Boolean {
        api.upsertAlert(
            payload = AlertRuleRequest(
                fundCode = code,
                horizon = horizon,
                minUpProbability = 0.6,
                minConfidence = 0.55,
                minExpectedReturnPct = 0.0,
                enabled = true,
            ),
        )
        return true
    }
}
