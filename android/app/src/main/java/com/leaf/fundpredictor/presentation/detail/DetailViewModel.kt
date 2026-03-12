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
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DetailUiState(
    val loading: Boolean = false,
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
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
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
                )
            }.onSuccess {
                _uiState.value = it
            }.onFailure { ex ->
                Log.e("DetailViewModel", "load failed, code=$code, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                _uiState.value = DetailUiState(error = "详情加载失败")
            }
        }
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
