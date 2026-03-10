package com.leaf.fundpredictor.presentation.detail

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.Explain
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.Prediction
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
    val quote: Quote? = null,
    val shortPred: Prediction? = null,
    val midPred: Prediction? = null,
    val explain: Explain? = null,
    val kline: List<KlineCandle> = emptyList(),
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
                val kline = repository.getKline(code, days = 60)
                DetailUiState(
                    quote = quote,
                    shortPred = shortPred,
                    midPred = midPred,
                    explain = explain,
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
        viewModelScope.launch {
            runCatching { repository.addWatchlist(code) }
                .onFailure { ex ->
                    Log.e("DetailViewModel", "add watchlist failed, code=$code, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                    _uiState.value = _uiState.value.copy(error = "加入自选失败")
                }
        }
    }
}
