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
    val nav: Double,
    val dailyChangePct: Double,
    val volatility20d: Double,
)

data class Prediction(
    val code: String,
    val horizon: String,
    val asOf: String,
    val dataFreshness: String,
    val upProbability: Double,
    val expectedReturnPct: Double,
    val confidence: Double,
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
