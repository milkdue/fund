package com.leaf.fundpredictor.data.remote

import com.squareup.moshi.Json
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

data class FundDto(val code: String, val name: String, val category: String)

data class QuoteDto(
    val code: String,
    @Json(name = "nav") val nav: Double,
    @Json(name = "daily_change_pct") val dailyChangePct: Double,
    @Json(name = "volatility_20d") val volatility20d: Double,
)

data class PredictionDto(
    val code: String,
    val horizon: String,
    @Json(name = "up_probability") val upProbability: Double,
    @Json(name = "expected_return_pct") val expectedReturnPct: Double,
    val confidence: Double,
)

data class ExplainFactorDto(val name: String, val contribution: Double)

data class ExplainDto(
    val code: String,
    val horizon: String,
    @Json(name = "confidence_interval_pct") val confidenceIntervalPct: List<Double>,
    @Json(name = "top_factors") val topFactors: List<ExplainFactorDto>,
)

data class WatchlistItemDto(
    @Json(name = "user_id") val userId: String,
    @Json(name = "fund_code") val fundCode: String,
)

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

    @GET("user/watchlist")
    suspend fun getWatchlist(@Header("X-User-Id") userId: String = "demo-user"): List<WatchlistItemDto>

    @POST("user/watchlist")
    suspend fun addWatchlist(
        @Body payload: WatchlistAddRequest,
        @Header("X-User-Id") userId: String = "demo-user",
    ): WatchlistItemDto
}
