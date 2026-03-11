package com.leaf.fundpredictor.data.repository

import com.leaf.fundpredictor.data.local.WatchlistDao
import com.leaf.fundpredictor.data.local.WatchlistEntity
import com.leaf.fundpredictor.data.remote.AlertRuleRequest
import com.leaf.fundpredictor.data.remote.FeedbackRequest
import com.leaf.fundpredictor.data.remote.FundApi
import com.leaf.fundpredictor.data.remote.WatchlistAddRequest
import com.leaf.fundpredictor.domain.model.AiJudgement
import com.leaf.fundpredictor.domain.model.AlertEvent
import com.leaf.fundpredictor.domain.model.AlertRule
import com.leaf.fundpredictor.domain.model.DataHealth
import com.leaf.fundpredictor.domain.model.Explain
import com.leaf.fundpredictor.domain.model.ExplainFactor
import com.leaf.fundpredictor.domain.model.Fund
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.domain.model.PredictionChange
import com.leaf.fundpredictor.domain.model.PredictionChangeFactor
import com.leaf.fundpredictor.domain.model.Quote
import com.leaf.fundpredictor.domain.model.ScoreCard
import com.leaf.fundpredictor.domain.model.ScoreComponent
import com.leaf.fundpredictor.domain.model.WatchlistInsight
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
        val scorecardDto = dto.scorecard
        return Prediction(
            dto.code,
            dto.horizon,
            dto.asOf,
            dto.dataFreshness,
            dto.upProbability,
            dto.expectedReturnPct,
            dto.confidence,
            dto.modelVersion,
            dto.dataSource,
            dto.snapshotId,
            ScoreCard(
                horizon = scorecardDto?.horizon ?: dto.horizon,
                totalScore = scorecardDto?.totalScore ?: ((dto.upProbability * 100).toInt()),
                riskScore = scorecardDto?.riskScore ?: (dto.confidence * 100).toInt(),
                actionLabel = scorecardDto?.actionLabel ?: "观察",
                signalBias = scorecardDto?.signalBias ?: "震荡",
                summary = scorecardDto?.summary ?: "当前后端尚未返回评分卡，先展示基础量化结果。",
                components = scorecardDto?.components?.map {
                    ScoreComponent(
                        key = it.key,
                        label = it.label,
                        score = it.score,
                        summary = it.summary,
                    )
                } ?: emptyList(),
            ),
        )
    }

    override suspend fun getPredictionChange(code: String, horizon: String): PredictionChange {
        val dto = api.getPredictionChange(code, horizon)
        return PredictionChange(
            code = dto.code,
            horizon = dto.horizon,
            currentAsOf = dto.currentAsOf,
            previousAsOf = dto.previousAsOf,
            dataFreshness = dto.dataFreshness,
            upProbabilityDelta = dto.upProbabilityDelta,
            expectedReturnPctDelta = dto.expectedReturnPctDelta,
            confidenceDelta = dto.confidenceDelta,
            changedFactors = dto.changedFactors.map {
                PredictionChangeFactor(
                    name = it.name,
                    before = it.before,
                    after = it.after,
                    delta = it.delta,
                )
            },
            summary = dto.summary,
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

    override suspend fun getAiJudgement(code: String, horizon: String): AiJudgement {
        val dto = api.getAiJudgement(code, horizon)
        return AiJudgement(
            code = dto.code,
            horizon = dto.horizon,
            asOf = dto.asOf,
            dataFreshness = dto.dataFreshness,
            trend = dto.trend,
            trendStrength = dto.trendStrength,
            agreementWithModel = dto.agreementWithModel,
            keyReasons = dto.keyReasons,
            riskWarnings = dto.riskWarnings,
            confidenceAdjustment = dto.confidenceAdjustment,
            adjustedUpProbability = dto.adjustedUpProbability,
            summary = dto.summary,
            provider = dto.provider,
            model = dto.model,
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

    override suspend fun getWatchlistInsights(): List<WatchlistInsight> {
        val dto = api.getWatchlistInsights()
        return dto.items.map {
            WatchlistInsight(
                fundCode = it.fundCode,
                shortUpProbability = it.shortUpProbability,
                shortConfidence = it.shortConfidence,
                midUpProbability = it.midUpProbability,
                midConfidence = it.midConfidence,
                shortScore = it.shortScore,
                midScore = it.midScore,
                riskScore = it.riskScore,
                actionLabel = it.actionLabel,
                scoreSummary = it.scoreSummary,
                dataFreshness = it.dataFreshness,
                riskLevel = it.riskLevel,
                signal = it.signal,
            )
        }
    }

    override suspend fun getDataHealth(): DataHealth {
        val dto = api.getDataHealth()
        return DataHealth(
            generatedAt = dto.generatedAt,
            fundPoolSize = dto.fundPoolSize,
            quoteCoverage48h = dto.quoteCoverage48h,
            predictionCoverage48h = dto.predictionCoverage48h,
            quoteFreshness = dto.quoteFreshness,
            predictionFreshness = dto.predictionFreshness,
            marketFreshness = dto.marketFreshness,
            sourceStatus = dto.sourceStatus,
        )
    }

    override suspend fun getAlertRules(): List<AlertRule> {
        return api.getAlertRules().map {
            AlertRule(
                id = it.id,
                userId = it.userId,
                fundCode = it.fundCode,
                horizon = it.horizon,
                enabled = it.enabled,
            )
        }
    }

    override suspend fun getAlertEvents(limit: Int): List<AlertEvent> {
        return api.getAlertEvents(limit = limit).map {
            AlertEvent(
                id = it.id,
                fundCode = it.fundCode,
                horizon = it.horizon,
                message = it.message,
                createdAt = it.createdAt,
            )
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
