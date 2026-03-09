package com.leaf.fundpredictor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.leaf.fundpredictor.presentation.nav.FundNavGraph
import com.leaf.fundpredictor.ui.theme.FundPredictorTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val prefs = AppPrefs(this)

        setContent {
            var riskAccepted by remember { mutableStateOf(prefs.isRiskAcknowledged()) }

            FundPredictorTheme {
                FundNavGraph(
                    riskAccepted = riskAccepted,
                    onRiskAccepted = {
                        prefs.setRiskAcknowledged(true)
                        riskAccepted = true
                    }
                )
            }
        }
    }
}
