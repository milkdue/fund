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
    @Json(name = "nav") val nav: Double,
    @Json(name = "daily_change_pct") val dailyChangePct: Double,
    @Json(name = "volatility_20d") val volatility20d: Double,
)

@JsonClass(generateAdapter = true)
data class PredictionDto(
    val code: String,
    val horizon: String,
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
    @Json(name = "confidence_interval_pct") val confidenceIntervalPct: List<Double>,
    @Json(name = "top_factors") val topFactors: List<ExplainFactorDto>,
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

    @GET("funds/{code}/kline")
    suspend fun getKline(@Path("code") code: String, @Query("days") days: Int = 60): KlineDto

    @GET("user/watchlist")
    suspend fun getWatchlist(@Header("X-User-Id") userId: String = "demo-user"): List<WatchlistItemDto>

    @POST("user/watchlist")
    suspend fun addWatchlist(
        @Body payload: WatchlistAddRequest,
        @Header("X-User-Id") userId: String = "demo-user",
    ): WatchlistItemDto
}
