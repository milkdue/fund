package com.leaf.fundpredictor.domain.usecase

import com.leaf.fundpredictor.domain.model.Explain
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.domain.model.Quote
import com.leaf.fundpredictor.domain.repository.FundRepository
import javax.inject.Inject

class GetPredictionsUseCase @Inject constructor(
    private val repository: FundRepository,
) {
    suspend fun execute(code: String): Triple<Quote, Prediction, Prediction> {
        val quote = repository.getQuote(code)
        val shortPred = repository.getPrediction(code, "short")
        val midPred = repository.getPrediction(code, "mid")
        return Triple(quote, shortPred, midPred)
    }

    suspend fun explain(code: String): Explain {
        return repository.getExplain(code, "short")
    }
}
