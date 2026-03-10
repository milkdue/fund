package com.leaf.fundpredictor

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.app.ActivityCompat
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
        requestNotificationPermissionIfNeeded()

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

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) return
        ActivityCompat.requestPermissions(
            this,
            arrayOf(Manifest.permission.POST_NOTIFICATIONS),
            1001,
        )
    }
}
