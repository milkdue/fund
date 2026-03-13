package com.leaf.fundpredictor.data.remote

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

@JsonClass(generateAdapter = true)
data class FundDto(val code: String, val name: String, val category: String)

@JsonClass(generateAdapter = true)
data class QuoteDto(
    val code: String,
    @Json(name = "as_of") val asOf: String,
    @Json(name = "data_freshness") val dataFreshness: String,
    @Json(name = "quote_type") val quoteType: String = "official_nav",
    val source: String = "eastmoney_pingzhongdata",
    @Json(name = "source_label") val sourceLabel: String = "东方财富正式净值",
    @Json(name = "quality_status") val qualityStatus: String = "ok",
    @Json(name = "quality_flags") val qualityFlags: List<String> = emptyList(),
    @Json(name = "nav") val nav: Double,
    @Json(name = "daily_change_pct") val dailyChangePct: Double,
    @Json(name = "volatility_20d") val volatility20d: Double,
)

@JsonClass(generateAdapter = true)
data class EstimateDto(
    val code: String,
    @Json(name = "as_of") val asOf: String,
    @Json(name = "data_freshness") val dataFreshness: String,
    @Json(name = "estimate_nav") val estimateNav: Double,
    @Json(name = "estimate_change_pct") val estimateChangePct: Double,
    @Json(name = "reference_nav") val referenceNav: Double? = null,
    @Json(name = "reference_nav_as_of") val referenceNavAsOf: String? = null,
    val source: String = "eastmoney_fundgz",
    @Json(name = "source_label") val sourceLabel: String = "东方财富盘中估值",
    @Json(name = "quality_status") val qualityStatus: String = "ok",
    @Json(name = "quality_flags") val qualityFlags: List<String> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class ScoreComponentDto(
    val key: String,
    val label: String,
    val score: Int,
    val summary: String,
    @Json(name = "detail_lines") val detailLines: List<String> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class ScoreCardDto(
    val horizon: String,
    @Json(name = "total_score") val totalScore: Int,
    @Json(name = "risk_score") val riskScore: Int,
    @Json(name = "action_label") val actionLabel: String,
    @Json(name = "signal_bias") val signalBias: String,
    val summary: String,
    val components: List<ScoreComponentDto>,
)

@JsonClass(generateAdapter = true)
data class PredictionDto(
    val code: String,
    val horizon: String,
    @Json(name = "as_of") val asOf: String,
    @Json(name = "data_freshness") val dataFreshness: String,
    @Json(name = "up_probability") val upProbability: Double,
    @Json(name = "expected_return_pct") val expectedReturnPct: Double,
    val confidence: Double,
    @Json(name = "model_version") val modelVersion: String = "unknown",
    @Json(name = "data_source") val dataSource: String = "rule_based",
    @Json(name = "snapshot_id") val snapshotId: String? = null,
    val scorecard: ScoreCardDto? = null,
)

@JsonClass(generateAdapter = true)
data class ExplainFactorDto(val name: String, val contribution: Double)

@JsonClass(generateAdapter = true)
data class ExplainDto(
    val code: String,
    val horizon: String,
    @Json(name = "data_freshness") val dataFreshness: String,
    @Json(name = "confidence_interval_pct") val confidenceIntervalPct: List<Double>,
    @Json(name = "top_factors") val topFactors: List<ExplainFactorDto>,
    @Json(name = "risk_flags") val riskFlags: List<String> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class AiJudgementDto(
    val code: String,
    val horizon: String,
    @Json(name = "as_of") val asOf: String,
    @Json(name = "data_freshness") val dataFreshness: String,
    val trend: String,
    @Json(name = "trend_strength") val trendStrength: Int,
    @Json(name = "agreement_with_model") val agreementWithModel: String,
    @Json(name = "key_reasons") val keyReasons: List<String>,
    @Json(name = "risk_warnings") val riskWarnings: List<String>,
    @Json(name = "confidence_adjustment") val confidenceAdjustment: Double,
    @Json(name = "adjusted_up_probability") val adjustedUpProbability: Double,
    val summary: String,
    val provider: String,
    val model: String,
)

@JsonClass(generateAdapter = true)
data class KlineItemDto(
    val ts: String,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
)

@JsonClass(generateAdapter = true)
data class KlineDto(
    val code: String,
    val items: List<KlineItemDto>,
)

@JsonClass(generateAdapter = true)
data class WatchlistItemDto(
    @Json(name = "user_id") val userId: String,
    @Json(name = "fund_code") val fundCode: String,
)

@JsonClass(generateAdapter = true)
data class PredictionChangeFactorDto(
    val name: String,
    val before: Double? = null,
    val after: Double? = null,
    val delta: Double,
)

@JsonClass(generateAdapter = true)
data class PredictionChangeDto(
    val code: String,
    val horizon: String,
    @Json(name = "current_as_of") val currentAsOf: String,
    @Json(name = "previous_as_of") val previousAsOf: String? = null,
    @Json(name = "data_freshness") val dataFreshness: String,
    @Json(name = "up_probability_delta") val upProbabilityDelta: Double,
    @Json(name = "expected_return_pct_delta") val expectedReturnPctDelta: Double,
    @Json(name = "confidence_delta") val confidenceDelta: Double,
    @Json(name = "changed_factors") val changedFactors: List<PredictionChangeFactorDto>,
    val summary: String,
)

@JsonClass(generateAdapter = true)
data class WatchlistInsightDto(
    @Json(name = "fund_code") val fundCode: String,
    @Json(name = "short_up_probability") val shortUpProbability: Double? = null,
    @Json(name = "short_confidence") val shortConfidence: Double? = null,
    @Json(name = "mid_up_probability") val midUpProbability: Double? = null,
    @Json(name = "mid_confidence") val midConfidence: Double? = null,
    @Json(name = "short_score") val shortScore: Int? = null,
    @Json(name = "mid_score") val midScore: Int? = null,
    @Json(name = "risk_score") val riskScore: Int? = null,
    @Json(name = "action_label") val actionLabel: String = "观察",
    @Json(name = "score_summary") val scoreSummary: String = "",
    @Json(name = "short_scorecard") val shortScorecard: ScoreCardDto? = null,
    @Json(name = "mid_scorecard") val midScorecard: ScoreCardDto? = null,
    @Json(name = "data_freshness") val dataFreshness: String,
    @Json(name = "risk_level") val riskLevel: String,
    val signal: String,
)

@JsonClass(generateAdapter = true)
data class WatchlistInsightsDto(
    @Json(name = "user_id") val userId: String,
    @Json(name = "generated_at") val generatedAt: String,
    val items: List<WatchlistInsightDto>,
)

@JsonClass(generateAdapter = true)
data class DataHealthDto(
    @Json(name = "generated_at") val generatedAt: String,
    @Json(name = "fund_pool_size") val fundPoolSize: Int,
    @Json(name = "quote_coverage_48h") val quoteCoverage48h: Double,
    @Json(name = "prediction_coverage_48h") val predictionCoverage48h: Double,
    @Json(name = "latest_estimate_at") val latestEstimateAt: String? = null,
    @Json(name = "quote_freshness") val quoteFreshness: String,
    @Json(name = "prediction_freshness") val predictionFreshness: String,
    @Json(name = "market_freshness") val marketFreshness: String,
    @Json(name = "source_status") val sourceStatus: Map<String, String> = emptyMap(),
)

@JsonClass(generateAdapter = true)
data class NewsSignalDto(
    val code: String,
    @Json(name = "trade_date") val tradeDate: String,
    @Json(name = "headline_count") val headlineCount: Int,
    @Json(name = "sentiment_score") val sentimentScore: Double,
    @Json(name = "event_score") val eventScore: Double,
    @Json(name = "volume_shock") val volumeShock: Double,
    @Json(name = "sample_title") val sampleTitle: String,
    @Json(name = "latest_published_at") val latestPublishedAt: String? = null,
    @Json(name = "latest_age_days") val latestAgeDays: Double? = null,
    @Json(name = "impact_strength") val impactStrength: String = "neutral",
    @Json(name = "impact_summary") val impactSummary: String = "",
)

@JsonClass(generateAdapter = true)
data class WatchlistAddRequest(@Json(name = "fund_code") val fundCode: String)

@JsonClass(generateAdapter = true)
data class FeedbackRequest(
    val horizon: String,
    @Json(name = "is_helpful") val isHelpful: Boolean,
    val score: Int = 3,
    val comment: String? = null,
)

@JsonClass(generateAdapter = true)
data class FeedbackDto(
    val id: Long,
    @Json(name = "user_id") val userId: String,
    @Json(name = "fund_code") val fundCode: String,
    val horizon: String,
    @Json(name = "is_helpful") val isHelpful: Boolean,
    val score: Int,
)

@JsonClass(generateAdapter = true)
data class AlertRuleRequest(
    @Json(name = "fund_code") val fundCode: String,
    val horizon: String = "short",
    @Json(name = "min_up_probability") val minUpProbability: Double = 0.6,
    @Json(name = "min_confidence") val minConfidence: Double = 0.55,
    @Json(name = "min_expected_return_pct") val minExpectedReturnPct: Double = 0.0,
    val enabled: Boolean = true,
)

@JsonClass(generateAdapter = true)
data class AlertRuleDto(
    val id: Long,
    @Json(name = "user_id") val userId: String,
    @Json(name = "fund_code") val fundCode: String,
    val horizon: String,
    @Json(name = "min_up_probability") val minUpProbability: Double,
    @Json(name = "min_confidence") val minConfidence: Double,
    @Json(name = "min_expected_return_pct") val minExpectedReturnPct: Double,
    val enabled: Boolean,
)

@JsonClass(generateAdapter = true)
data class AlertEventDto(
    val id: Long,
    @Json(name = "fund_code") val fundCode: String,
    val horizon: String,
    val message: String,
    @Json(name = "created_at") val createdAt: String,
)

interface FundApi {
    @GET("funds/search")
    suspend fun searchFunds(@Query("q") q: String): List<FundDto>

    @GET("funds/hot")
    suspend fun hotFunds(): List<FundDto>

    @GET("funds/{code}/quote")
    suspend fun getQuote(@Path("code") code: String): QuoteDto

    @GET("funds/{code}/estimate")
    suspend fun getEstimate(@Path("code") code: String): EstimateDto

    @GET("funds/{code}/predict")
    suspend fun getPrediction(@Path("code") code: String, @Query("horizon") horizon: String): PredictionDto

    @GET("funds/{code}/prediction-change")
    suspend fun getPredictionChange(@Path("code") code: String, @Query("horizon") horizon: String): PredictionChangeDto

    @GET("funds/{code}/explain")
    suspend fun getExplain(@Path("code") code: String, @Query("horizon") horizon: String): ExplainDto

    @GET("funds/{code}/ai-judgement")
    suspend fun getAiJudgement(@Path("code") code: String, @Query("horizon") horizon: String): AiJudgementDto

    @GET("funds/{code}/kline")
    suspend fun getKline(@Path("code") code: String, @Query("days") days: Int = 60): KlineDto

    @GET("funds/{code}/news-signal")
    suspend fun getNewsSignal(@Path("code") code: String): NewsSignalDto

    @GET("user/watchlist")
    suspend fun getWatchlist(@Header("X-User-Id") userId: String = "demo-user"): List<WatchlistItemDto>

    @GET("user/watchlist/insights")
    suspend fun getWatchlistInsights(@Header("X-User-Id") userId: String = "demo-user"): WatchlistInsightsDto

    @GET("system/data-health")
    suspend fun getDataHealth(): DataHealthDto

    @POST("user/watchlist")
    suspend fun addWatchlist(
        @Body payload: WatchlistAddRequest,
        @Header("X-User-Id") userId: String = "demo-user",
    ): WatchlistItemDto

    @POST("funds/{code}/feedback")
    suspend fun postFeedback(
        @Path("code") code: String,
        @Body payload: FeedbackRequest,
        @Header("X-User-Id") userId: String = "demo-user",
    ): FeedbackDto

    @POST("user/alerts")
    suspend fun upsertAlert(
        @Body payload: AlertRuleRequest,
        @Header("X-User-Id") userId: String = "demo-user",
    ): AlertRuleDto

    @GET("user/alerts")
    suspend fun getAlertRules(
        @Header("X-User-Id") userId: String = "demo-user",
    ): List<AlertRuleDto>

    @GET("user/alerts/events")
    suspend fun getAlertEvents(
        @Query("limit") limit: Int = 30,
        @Header("X-User-Id") userId: String = "demo-user",
    ): List<AlertEventDto>
}
