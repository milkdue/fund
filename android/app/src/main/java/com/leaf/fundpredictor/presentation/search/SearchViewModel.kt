package com.leaf.fundpredictor.presentation.search

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.leaf.fundpredictor.domain.model.DataHealth
import com.leaf.fundpredictor.domain.model.Fund
import com.leaf.fundpredictor.domain.repository.FundRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SearchUiState(
    val query: String = "",
    val items: List<Fund> = emptyList(),
    val loading: Boolean = false,
    val dataHealth: DataHealth? = null,
    val error: String? = null,
)

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val repository: FundRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()

    fun onQueryChange(value: String) {
        _uiState.value = _uiState.value.copy(query = value)
    }

    fun search() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            val query = _uiState.value.query.trim()
            runCatching {
                if (query.isBlank()) repository.hotFunds() else repository.searchFunds(query)
            }
                .onSuccess { funds ->
                    val health = runCatching { repository.getDataHealth() }
                        .onFailure { ex ->
                            Log.w("SearchViewModel", "data health failed, type=${ex::class.java.simpleName}, msg=${ex.message}")
                        }
                        .getOrNull()
                    _uiState.value = _uiState.value.copy(
                        loading = false,
                        items = funds,
                        dataHealth = health ?: _uiState.value.dataHealth,
                    )
                }
                .onFailure { ex ->
                    Log.e("SearchViewModel", "search failed, query=$query, type=${ex::class.java.simpleName}, msg=${ex.message}", ex)
                    _uiState.value = _uiState.value.copy(loading = false, error = "搜索失败，请稍后再试")
                }
        }
    }
}
