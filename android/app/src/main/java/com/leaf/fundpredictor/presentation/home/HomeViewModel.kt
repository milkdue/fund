package com.leaf.fundpredictor.presentation.home

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.DataHealth
import com.leaf.fundpredictor.domain.model.AlertRule
import com.leaf.fundpredictor.domain.model.WatchlistInsight
import com.leaf.fundpredictor.domain.repository.FundRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val loading: Boolean = false,
    val refreshing: Boolean = false,
    val dataHealth: DataHealth? = null,
    val topInsights: List<WatchlistInsight> = emptyList(),
    val alertFundCodes: Set<String> = emptySet(),
    val lastRefreshedAt: String? = null,
    val error: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: FundRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    fun load() {
        loadInternal(preserveContent = false)
    }

    fun refresh() {
        if (_uiState.value.loading || _uiState.value.refreshing) return
        loadInternal(preserveContent = true)
    }

    private fun loadInternal(preserveContent: Boolean) {
        if (_uiState.value.loading && !preserveContent) return
        viewModelScope.launch {
            _uiState.value = if (preserveContent) {
                _uiState.value.copy(refreshing = true, error = null)
            } else {
                _uiState.value.copy(loading = true, refreshing = false, error = null)
            }

            val health = runCatching { repository.getDataHealth() }
                .onFailure { ex ->
                    Log.e(
                        "HomeViewModel",
                        "data health failed, type=${ex::class.java.simpleName}, msg=${ex.message}",
                        ex,
                    )
                }
                .getOrNull()
            val alertFundCodes = runCatching { repository.getAlertRules() }
                .getOrDefault(emptyList<AlertRule>())
                .asSequence()
                .filter { it.enabled }
                .map { it.fundCode }
                .toSet()
            val topInsights = runCatching { repository.getWatchlistInsights() }
                .onFailure { ex ->
                    Log.e(
                        "HomeViewModel",
                        "watchlist insights failed, type=${ex::class.java.simpleName}, msg=${ex.message}",
                        ex,
                    )
                }
                .getOrDefault(emptyList())
                .sortedWith(
                    compareBy<WatchlistInsight> { actionPriority(it.actionLabel) }
                        .thenByDescending { it.shortScore ?: Int.MIN_VALUE }
                        .thenByDescending { it.midScore ?: Int.MIN_VALUE }
                        .thenByDescending { it.riskScore ?: Int.MIN_VALUE }
                        .thenBy { freshnessPriority(it.dataFreshness) }
                        .thenBy { it.fundCode }
                )
                .take(3)

            _uiState.value = _uiState.value.copy(
                loading = false,
                refreshing = false,
                dataHealth = health,
                topInsights = topInsights,
                alertFundCodes = alertFundCodes,
                lastRefreshedAt = nowLabel(),
                error = if (health == null) "首页数据暂时不可用，请稍后重试" else null,
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
}
