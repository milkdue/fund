package com.leaf.fundpredictor.presentation.home

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.DataHealth
import com.leaf.fundpredictor.domain.repository.FundRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val loading: Boolean = false,
    val dataHealth: DataHealth? = null,
    val error: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: FundRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    fun load() {
        if (_uiState.value.loading) return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)

            val health = runCatching { repository.getDataHealth() }
                .onFailure { ex ->
                    Log.e(
                        "HomeViewModel",
                        "data health failed, type=${ex::class.java.simpleName}, msg=${ex.message}",
                        ex,
                    )
                }
                .getOrNull()

            _uiState.value = _uiState.value.copy(
                loading = false,
                dataHealth = health,
                error = if (health == null) "首页数据暂时不可用，请稍后重试" else null,
            )
        }
    }
}
