package com.leaf.fundpredictor

import com.leaf.fundpredictor.domain.usecase.ValidateRiskAcknowledgementUseCase
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ValidateRiskAcknowledgementUseCaseTest {
    private val useCase = ValidateRiskAcknowledgementUseCase()

    @Test
    fun acknowledged_true_allows_entry() {
        assertTrue(useCase.canEnterMainFlow(true))
    }

    @Test
    fun acknowledged_false_blocks_entry() {
        assertFalse(useCase.canEnterMainFlow(false))
    }
}
