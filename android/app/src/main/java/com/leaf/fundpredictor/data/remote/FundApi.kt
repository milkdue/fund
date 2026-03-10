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
    @Json(name = "nav") val nav: Double,
    @Json(name = "daily_change_pct") val dailyChangePct: Double,
    @Json(name = "volatility_20d") val volatility20d: Double,
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

interface FundApi {
    @GET("funds/search")
    suspend fun searchFunds(@Query("q") q: String): List<FundDto>

    @GET("funds/hot")
    suspend fun hotFunds(): List<FundDto>

    @GET("funds/{code}/quote")
    suspend fun getQuote(@Path("code") code: String): QuoteDto

    @GET("funds/{code}/predict")
    suspend fun getPrediction(@Path("code") code: String, @Query("horizon") horizon: String): PredictionDto

    @GET("funds/{code}/explain")
    suspend fun getExplain(@Path("code") code: String, @Query("horizon") horizon: String): ExplainDto

    @GET("funds/{code}/ai-judgement")
    suspend fun getAiJudgement(@Path("code") code: String, @Query("horizon") horizon: String): AiJudgementDto

    @GET("funds/{code}/kline")
    suspend fun getKline(@Path("code") code: String, @Query("days") days: Int = 60): KlineDto

    @GET("user/watchlist")
    suspend fun getWatchlist(@Header("X-User-Id") userId: String = "demo-user"): List<WatchlistItemDto>

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
}
