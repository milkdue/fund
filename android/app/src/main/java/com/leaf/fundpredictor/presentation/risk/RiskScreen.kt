package com.leaf.fundpredictor.presentation.risk

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Gavel
import androidx.compose.material.icons.rounded.Newspaper
import androidx.compose.material.icons.rounded.WarningAmber
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.presentation.components.MotionReveal

@Composable
fun RiskScreen(onAgree: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                brush = Brush.verticalGradient(
                    colors = listOf(Color(0xFFE7F1FF), Color(0xFFF2FFF7), Color(0xFFF8F9FE))
                )
            )
            .padding(20.dp)
    ) {
        Column(
            modifier = Modifier.align(Alignment.Center),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            MotionReveal(delayMs = 40) {
                Text("Fund Predictor", style = MaterialTheme.typography.displaySmall, color = Color(0xFF0E3A66))
            }
            MotionReveal(delayMs = 90) {
                Text("风险与合规确认", style = MaterialTheme.typography.titleLarge)
            }
            MotionReveal(delayMs = 130) {
                Text(
                    "请确认你理解：预测仅用于辅助研究，不构成任何投资建议。",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            MotionReveal(delayMs = 180) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(defaultElevation = 6.dp),
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        RiskLine(
                            icon = Icons.Rounded.Newspaper,
                            text = "本应用仅供学习研究，不构成投资建议。",
                        )
                        RiskLine(
                            icon = Icons.Rounded.WarningAmber,
                            text = "基金有风险，模型输出可能和真实市场偏离。",
                        )
                        RiskLine(
                            icon = Icons.Rounded.Gavel,
                            text = "禁止保本、保收益、确定性买卖点承诺。",
                        )
                    }
                }
            }

            MotionReveal(delayMs = 240) {
                Button(onClick = onAgree, modifier = Modifier.fillMaxWidth()) {
                    Text("我已阅读并同意继续")
                }
            }
        }
    }
}

@Composable
private fun RiskLine(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    text: String,
) {
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.Top) {
        Icon(icon, contentDescription = null, tint = Color(0xFF0C5B9F))
        Text(text, modifier = Modifier.weight(1f))
    }
}
