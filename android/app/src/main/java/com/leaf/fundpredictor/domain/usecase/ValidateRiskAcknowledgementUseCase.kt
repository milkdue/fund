package com.leaf.fundpredictor.domain.usecase

import javax.inject.Inject

class ValidateRiskAcknowledgementUseCase @Inject constructor() {
    fun canEnterMainFlow(acknowledged: Boolean): Boolean = acknowledged
}
