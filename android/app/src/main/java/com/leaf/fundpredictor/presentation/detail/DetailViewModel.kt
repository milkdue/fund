package com.leaf.fundpredictor.presentation.detail

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.AiJudgement
import com.leaf.fundpredictor.domain.model.Explain
import com.leaf.fundpredictor.domain.model.Estimate
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.NewsSignal
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.domain.model.PredictionChange
import com.leaf.fundpredictor.domain.model.Quote
import com.leaf.fundpredictor.domain.repository.FundRepository
import com.leaf.fundpredictor.domain.usecase.GetPredictionsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DetailUiState(
    val loading: Boolean = false,
    val refreshing: Boolean = false,
    val isAddingWatchlist: Boolean = false,
    val isSettingAlert: Boolean = false,
    val isWatchlisted: Boolean = false,
    val hasAlertConfigured: Boolean = false,
    val quote: Quote? = null,
    val estimate: Estimate? = null,
    val shortPred: Prediction? = null,
    val midPred: Prediction? = null,
    val shortAi: AiJudgement? = null,
    val midAi: AiJudgement? = null,
    val explain: Explain? = null,
    val newsSignal: NewsSignal? = null,
    val shortChange: PredictionChange? = null,
    val kline: List<KlineCandle> = emptyList(),
    val lastRefreshedAt: String? = null,
    val refreshSummary: String? = null,
    val refreshDetails: List<String> = emptyList(),
    val notice: String? = null,
    val error: String? = null,
)

@HiltViewModel
class DetailViewModel @Inject constructor(
    private val useCase: GetPredictionsUseCase,
    private val repository: FundRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(DetailUiState())
    val uiState: StateFlow<DetailUiState> = _uiState.asStateFlow()

    fun load(code: String) {
        loadInternal(code = code, preserveContent = false)
    }

    fun refresh(code: String) {
        if (_uiState.value.loading || _uiState.value.refreshing) return
        loadInternal(code = code, preserveContent = true)
    }

    private fun loadInternal(code: String, preserveContent: Boolean) {
        viewModelScope.launch {
            val previousState = _uiState.value
            _uiState.value = if (preserveContent) {
                _uiState.value.copy(refreshing = true, error = null, notice = null)
            } else {
                _uiState.value.copy(loading = true, refreshing = false, error = null, notice = null)
            }
            runCatching {
                val (quote, shortPred, midPred) = useCase.execute(code)
                val explain = useCase.explain(code)
                val estimate = runCatching { repository.getEstimate(code) }.getOrNull()
                val newsSignal = runCatching { repository.getNewsSignal(code) }.getOrNull()
                val shortChange = runCatching { repository.getPredictionChange(code, "short") }.getOrNull()
                val kline = repository.getKline(code, days = 60)
                val shortAi = runCatching { repository.getAiJudgement(code, "short") }.getOrNull()
                val midAi = runCatching { repository.getAiJudgement(code, "mid") }.getOrNull()
                val watchlistCodes = runCatching { repository.getWatchlist() }
                    .getOrDefault(emptyList())
                    .asSequence()
                    .map { it.fundCode }
                    .toSet()
                val alertCodes = runCatching { repository.getAlertRules() }
                    .getOrDefault(emptyList())
                    .asSequence()
                    .filter { it.enabled }
                    .map { it.fundCode }
                    .toSet()
                DetailUiState(
                    isWatchlisted = watchlistCodes.contains(code),
                    hasAlertConfigured = alertCodes.contains(code),
                    loading = false,
                    quote = quote,
                    estimate = estimate,
                    shortPred = shortPred,
                    midPred = midPred,
                    shortAi = shortAi,
                    midAi = midAi,
                    explain = explain,
                    newsSignal = newsSignal,
                    shortChange = shortChange,
                    kline = kline,
                    lastRefreshedAt = nowLabel(),
                    refreshSummary = if (preserveContent) buildRefreshSummary(previousState, shortPred, midPred) else null,
                    refreshDetails = if (preserveContent) buildRefreshDetails(previousState, quote, estimate, newsSignal, shortPred, midPred) else emptyList(),
                    refreshing = false,
                )
            }.onSuccess {
                _uiState.value = it
            }.onFailure { ex ->
                Log.e("DetailViewModel", "load failed, code=$code, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                _uiState.value = if (preserveContent) {
                    _uiState.value.copy(
                        refreshing = false,
                        error = "刷新失败，已保留当前内容",
                    )
                } else {
                    DetailUiState(error = "详情加载失败")
                }
            }
        }
    }

    private fun buildRefreshSummary(
        previousState: DetailUiState,
        shortPred: Prediction?,
        midPred: Prediction?,
    ): String {
        val shortChanged = predictionChanged(previousState.shortPred, shortPred)
        val midChanged = predictionChanged(previousState.midPred, midPred)
        return when {
            shortChanged && midChanged -> "本次刷新拿到了新的短期和中期快照。"
            shortChanged -> "本次刷新拿到了新的短期快照。"
            midChanged -> "本次刷新拿到了新的中期快照。"
            else -> "本次刷新未发现新的预测快照，当前主要是同步最新说明项和行情状态。"
        }
    }

    private fun buildRefreshDetails(
        previousState: DetailUiState,
        quote: Quote?,
        estimate: Estimate?,
        newsSignal: NewsSignal?,
        shortPred: Prediction?,
        midPred: Prediction?,
    ): List<String> {
        val changes = buildList {
            if (quote != null && quote.asOf != previousState.quote?.asOf) {
                add("正式净值时间更新为 ${quote.asOf}")
            }
            if (estimate != null) {
                val previousEstimate = previousState.estimate
                when {
                    previousEstimate == null -> add("盘中估值数据已补齐")
                    estimate.asOf != previousEstimate.asOf -> add("盘中估值时间更新为 ${estimate.asOf}")
                    estimate.estimateNav != previousEstimate.estimateNav -> add("盘中估值数值发生变化")
                }
            }
            if (newsSignal != null) {
                when {
                    newsSignal.latestPublishedAt != previousState.newsSignal?.latestPublishedAt ->
                        add("公告/舆情样本出现了更新")
                    newsSignal.impactStrength != previousState.newsSignal?.impactStrength ->
                        add("新闻影响强弱由 ${newsImpactText(previousState.newsSignal?.impactStrength)} 变为 ${newsImpactText(newsSignal.impactStrength)}")
                }
            }
            if (predictionChanged(previousState.shortPred, shortPred)) {
                add("短期预测快照已更新")
            } else if (shortPred != null && previousState.shortPred != null) {
                if (shortPred.upProbability != previousState.shortPred.upProbability) {
                    add("短期上涨概率有调整")
                }
            }
            if (predictionChanged(previousState.midPred, midPred)) {
                add("中期预测快照已更新")
            } else if (midPred != null && previousState.midPred != null) {
                if (midPred.upProbability != previousState.midPred.upProbability) {
                    add("中期上涨概率有调整")
                }
            }
        }
        return changes.take(4)
    }

    private fun predictionChanged(before: Prediction?, after: Prediction?): Boolean {
        if (before == null || after == null) return false
        return before.snapshotId != after.snapshotId || before.asOf != after.asOf
    }

    private fun newsImpactText(value: String?): String {
        return when ((value ?: "").lowercase()) {
            "strong" -> "强"
            "medium" -> "中"
            "weak" -> "弱"
            else -> "中性"
        }
    }

    private fun nowLabel(): String {
        return LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"))
    }

    fun addWatchlist(code: String) {
        if (_uiState.value.isAddingWatchlist || _uiState.value.isWatchlisted) return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isAddingWatchlist = true,
                notice = null,
                error = null,
            )
            runCatching { repository.addWatchlist(code) }
                .onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isAddingWatchlist = false,
                        isWatchlisted = true,
                        notice = "已加入自选",
                    )
                }
                .onFailure { ex ->
                    Log.e("DetailViewModel", "add watchlist failed, code=$code, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                    _uiState.value = _uiState.value.copy(
                        isAddingWatchlist = false,
                        error = "加入自选失败",
                    )
                }
        }
    }

    fun submitFeedback(code: String, horizon: String, isHelpful: Boolean) {
        viewModelScope.launch {
            runCatching { repository.submitFeedback(code, horizon, isHelpful, if (isHelpful) 5 else 2) }
                .onSuccess {
                    _uiState.value = _uiState.value.copy(notice = "反馈已提交")
                }
                .onFailure { ex ->
                    Log.e("DetailViewModel", "feedback failed, code=$code, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                    _uiState.value = _uiState.value.copy(error = "反馈提交失败")
                }
        }
    }

    fun setDefaultAlert(code: String, horizon: String = "short") {
        if (_uiState.value.isSettingAlert || _uiState.value.hasAlertConfigured) return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isSettingAlert = true,
                notice = null,
                error = null,
            )
            runCatching { repository.upsertDefaultAlert(code, horizon) }
                .onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isSettingAlert = false,
                        hasAlertConfigured = true,
                        notice = "已添加提醒阈值",
                    )
                }
                .onFailure { ex ->
                    Log.e("DetailViewModel", "alert upsert failed, code=$code, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                    _uiState.value = _uiState.value.copy(
                        isSettingAlert = false,
                        error = "提醒设置失败",
                    )
                }
        }
    }

    fun consumeNotice() {
        _uiState.value = _uiState.value.copy(notice = null)
    }

    fun consumeError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
