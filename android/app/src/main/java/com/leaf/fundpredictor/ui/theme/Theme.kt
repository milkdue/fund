package com.leaf.fundpredictor.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val AppLightColors = lightColorScheme(
    primary = Color(0xFF005B4F),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFF7CE7D0),
    onPrimaryContainer = Color(0xFF00201B),
    secondary = Color(0xFF4E635E),
    onSecondary = Color(0xFFFFFFFF),
    background = Color(0xFFF4FBF8),
    onBackground = Color(0xFF171D1B),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF171D1B),
    surfaceVariant = Color(0xFFE9F2EE),
    onSurfaceVariant = Color(0xFF39433F),
    error = Color(0xFFBA1A1A),
)

@Composable
fun FundPredictorTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = AppLightColors,
        typography = Typography(),
        content = content,
    )
}
