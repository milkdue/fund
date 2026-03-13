package com.leaf.fundpredictor.presentation.watchlist

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.WatchlistInsight
import com.leaf.fundpredictor.domain.model.WatchlistItem
import com.leaf.fundpredictor.domain.repository.FundRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class WatchlistUiState(
    val loading: Boolean = false,
    val refreshing: Boolean = false,
    val items: List<WatchlistItem> = emptyList(),
    val insights: List<WatchlistInsight> = emptyList(),
    val alertFundCodes: Set<String> = emptySet(),
    val diagnosticsNote: String? = null,
    val lastRefreshedAt: String? = null,
)

@HiltViewModel
class WatchlistViewModel @Inject constructor(
    private val repository: FundRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(WatchlistUiState())
    val uiState: StateFlow<WatchlistUiState> = _uiState.asStateFlow()

    fun load() {
        loadInternal(preserveContent = false)
    }

    fun refresh() {
        if (_uiState.value.loading || _uiState.value.refreshing) return
        loadInternal(preserveContent = true)
    }

    private fun loadInternal(preserveContent: Boolean) {
        viewModelScope.launch {
            _uiState.value = if (preserveContent) {
                _uiState.value.copy(refreshing = true)
            } else {
                _uiState.value.copy(loading = true, refreshing = false)
            }
            val insights = runCatching { repository.getWatchlistInsights() }
                .onFailure { ex ->
                    Log.e("WatchlistViewModel", "insights failed, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                }
                .getOrDefault(emptyList())
                .sortedWith(
                    compareBy<WatchlistInsight> { actionPriority(it.actionLabel) }
                        .thenByDescending { it.shortScore ?: Int.MIN_VALUE }
                        .thenByDescending { it.midScore ?: Int.MIN_VALUE }
                        .thenByDescending { it.riskScore ?: Int.MIN_VALUE }
                        .thenBy { freshnessPriority(it.dataFreshness) }
                        .thenBy { signalPriority(it.signal) }
                        .thenBy { it.fundCode }
                )
            val rows = runCatching { repository.getWatchlist() }
                .onFailure { ex ->
                    Log.e("WatchlistViewModel", "load failed, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                }
                .getOrDefault(emptyList())
                .sortedBy { it.fundCode }
            val alertFundCodes = runCatching { repository.getAlertRules() }
                .onFailure { ex ->
                    Log.e("WatchlistViewModel", "alert rules failed, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                }
                .getOrDefault(emptyList())
                .asSequence()
                .filter { it.enabled }
                .map { it.fundCode }
                .toSet()
            _uiState.value = _uiState.value.copy(
                loading = false,
                refreshing = false,
                items = rows,
                insights = insights,
                alertFundCodes = alertFundCodes,
                diagnosticsNote = if (insights.isEmpty() && rows.isNotEmpty()) "洞察数据暂不可用，展示本地自选列表" else null,
                lastRefreshedAt = nowLabel(),
            )
        }
    }

    private fun nowLabel(): String {
        return LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"))
    }

    private fun actionPriority(value: String): Int {
        return when (value) {
            "强关注" -> 0
            "关注" -> 1
            "观察" -> 2
            "回避" -> 3
            else -> 4
        }
    }

    private fun freshnessPriority(value: String): Int {
        return when (value.lowercase()) {
            "fresh" -> 0
            "lagging" -> 1
            "stale" -> 2
            else -> 3
        }
    }

    private fun signalPriority(value: String): Int {
        return when {
            value.contains("偏多") -> 0
            value.contains("震荡") -> 1
            value.contains("偏空") -> 2
            else -> 3
        }
    }
}
