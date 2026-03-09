package com.leaf.fundpredictor.presentation.risk

import androidx.lifecycle.ViewModel
import com.leaf.fundpredictor.domain.usecase.ValidateRiskAcknowledgementUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

@HiltViewModel
class RiskViewModel @Inject constructor(
    private val validateUseCase: ValidateRiskAcknowledgementUseCase,
) : ViewModel() {

    private val _ack = MutableStateFlow(false)
    val ack: StateFlow<Boolean> = _ack.asStateFlow()

    fun acknowledge() {
        _ack.value = validateUseCase.canEnterMainFlow(true)
    }
}
