package com.leaf.fundpredictor.presentation.alerts

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.AlertEvent
import com.leaf.fundpredictor.domain.repository.FundRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class AlertsUiState(
    val loading: Boolean = false,
    val items: List<AlertEvent> = emptyList(),
    val error: String? = null,
)

@HiltViewModel
class AlertsViewModel @Inject constructor(
    private val repository: FundRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(AlertsUiState())
    val uiState: StateFlow<AlertsUiState> = _uiState.asStateFlow()

    fun load() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            runCatching { repository.getAlertEvents(limit = 100) }
                .onSuccess { events ->
                    _uiState.value = _uiState.value.copy(
                        loading = false,
                        items = events,
                    )
                }
                .onFailure { ex ->
                    Log.e(
                        "AlertsViewModel",
                        "load failed, type=${ex::class.java.simpleName}, msg=${ex.message}",
                        ex,
                    )
                    _uiState.value = _uiState.value.copy(
                        loading = false,
                        error = "推送列表加载失败，请稍后再试",
                    )
                }
        }
    }
}
