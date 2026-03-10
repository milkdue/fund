package com.leaf.fundpredictor.presentation.watchlist

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.WatchlistInsight
import com.leaf.fundpredictor.domain.model.WatchlistItem
import com.leaf.fundpredictor.domain.repository.FundRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class WatchlistUiState(
    val loading: Boolean = false,
    val items: List<WatchlistItem> = emptyList(),
    val insights: List<WatchlistInsight> = emptyList(),
    val diagnosticsNote: String? = null,
)

@HiltViewModel
class WatchlistViewModel @Inject constructor(
    private val repository: FundRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(WatchlistUiState())
    val uiState: StateFlow<WatchlistUiState> = _uiState.asStateFlow()

    fun load() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true)
            val insights = runCatching { repository.getWatchlistInsights() }
                .onFailure { ex ->
                    Log.e("WatchlistViewModel", "insights failed, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                }
                .getOrDefault(emptyList())
            val rows = runCatching { repository.getWatchlist() }
                .onFailure { ex ->
                    Log.e("WatchlistViewModel", "load failed, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                }
                .getOrDefault(emptyList())
            _uiState.value = _uiState.value.copy(
                loading = false,
                items = rows,
                insights = insights,
                diagnosticsNote = if (insights.isEmpty() && rows.isNotEmpty()) "洞察数据暂不可用，展示本地自选列表" else null,
            )
        }
    }
}
