package com.leaf.fundpredictor.domain.model

data class Fund(
    val code: String,
    val name: String,
    val category: String,
)

data class Quote(
    val code: String,
    val asOf: String,
    val dataFreshness: String,
    val quoteType: String,
    val source: String,
    val sourceLabel: String,
    val qualityStatus: String,
    val qualityFlags: List<String>,
    val nav: Double,
    val dailyChangePct: Double,
    val volatility20d: Double,
)

data class Estimate(
    val code: String,
    val asOf: String,
    val dataFreshness: String,
    val estimateNav: Double,
    val estimateChangePct: Double,
    val referenceNav: Double?,
    val referenceNavAsOf: String?,
    val source: String,
    val sourceLabel: String,
    val qualityStatus: String,
    val qualityFlags: List<String>,
)

data class Prediction(
    val code: String,
    val horizon: String,
    val asOf: String,
    val dataFreshness: String,
    val upProbability: Double,
    val expectedReturnPct: Double,
    val confidence: Double,
    val modelVersion: String,
    val dataSource: String,
    val snapshotId: String?,
    val scorecard: ScoreCard,
)

data class ScoreComponent(
    val key: String,
    val label: String,
    val score: Int,
    val summary: String,
    val detailLines: List<String>,
)

data class ScoreCard(
    val horizon: String,
    val totalScore: Int,
    val riskScore: Int,
    val actionLabel: String,
    val signalBias: String,
    val summary: String,
    val components: List<ScoreComponent>,
)

data class ExplainFactor(
    val name: String,
    val contribution: Double,
)

data class Explain(
    val code: String,
    val horizon: String,
    val dataFreshness: String,
    val confidenceIntervalPct: Pair<Double, Double>,
    val topFactors: List<ExplainFactor>,
    val riskFlags: List<String>,
)

data class AiJudgement(
    val code: String,
    val horizon: String,
    val asOf: String,
    val dataFreshness: String,
    val trend: String,
    val trendStrength: Int,
    val agreementWithModel: String,
    val keyReasons: List<String>,
    val riskWarnings: List<String>,
    val confidenceAdjustment: Double,
    val adjustedUpProbability: Double,
    val summary: String,
    val provider: String,
    val model: String,
)

data class KlineCandle(
    val ts: String,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
)

data class WatchlistItem(
    val userId: String,
    val fundCode: String,
)

data class PredictionChangeFactor(
    val name: String,
    val before: Double?,
    val after: Double?,
    val delta: Double,
)

data class PredictionChange(
    val code: String,
    val horizon: String,
    val currentAsOf: String,
    val previousAsOf: String?,
    val dataFreshness: String,
    val upProbabilityDelta: Double,
    val expectedReturnPctDelta: Double,
    val confidenceDelta: Double,
    val changedFactors: List<PredictionChangeFactor>,
    val summary: String,
)

data class WatchlistInsight(
    val fundCode: String,
    val shortUpProbability: Double?,
    val shortConfidence: Double?,
    val midUpProbability: Double?,
    val midConfidence: Double?,
    val shortScore: Int?,
    val midScore: Int?,
    val riskScore: Int?,
    val actionLabel: String,
    val scoreSummary: String,
    val shortScorecard: ScoreCard?,
    val midScorecard: ScoreCard?,
    val dataFreshness: String,
    val riskLevel: String,
    val signal: String,
)

data class DataHealth(
    val generatedAt: String,
    val fundPoolSize: Int,
    val quoteCoverage48h: Double,
    val predictionCoverage48h: Double,
    val latestEstimateAt: String?,
    val quoteFreshness: String,
    val predictionFreshness: String,
    val marketFreshness: String,
    val sourceStatus: Map<String, String>,
)

data class NewsSignal(
    val code: String,
    val tradeDate: String,
    val headlineCount: Int,
    val sentimentScore: Double,
    val eventScore: Double,
    val volumeShock: Double,
    val sampleTitle: String,
)

data class AlertEvent(
    val id: Long,
    val fundCode: String,
    val horizon: String,
    val message: String,
    val createdAt: String,
)

data class AlertRule(
    val id: Long,
    val userId: String,
    val fundCode: String,
    val horizon: String,
    val enabled: Boolean,
)
