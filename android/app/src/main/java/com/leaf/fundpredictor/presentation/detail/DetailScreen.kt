package com.leaf.fundpredictor.presentation.detail

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.TrendingUp
import androidx.compose.material.icons.rounded.AddAlert
import androidx.compose.material.icons.rounded.NotificationsActive
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.AiJudgement
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.domain.model.Quote
import com.leaf.fundpredictor.presentation.components.ListSkeleton
import com.leaf.fundpredictor.presentation.components.MotionReveal
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DetailScreen(code: String, viewModel: DetailViewModel, onBack: () -> Unit) {
    val state by viewModel.uiState.collectAsState()
    val shortAi = state.shortAi
    val midAi = state.midAi

    LaunchedEffect(code) { viewModel.load(code) }

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("基金详情")
                        Text("代码 $code", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Rounded.ArrowBack, contentDescription = "back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent),
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    brush = Brush.verticalGradient(
                        colors = listOf(Color(0xFFEBF4FF), Color(0xFFF5FFF8), Color(0xFFF6F8FD))
                    )
                )
                .padding(innerPadding)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                MotionReveal(delayMs = 40) {
                    OverviewSignalCard(
                        shortPred = state.shortPred,
                        midPred = state.midPred,
                    )
                }

                MotionReveal(delayMs = 110) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                        FilledTonalButton(
                            modifier = Modifier.weight(1f),
                            onClick = { viewModel.addWatchlist(code) },
                        ) {
                            Icon(Icons.Rounded.Star, contentDescription = "watch")
                            Text("加入自选", modifier = Modifier.padding(start = 6.dp))
                        }
                        OutlinedButton(
                            modifier = Modifier.weight(1f),
                            onClick = { viewModel.setDefaultAlert(code) },
                        ) {
                            Icon(Icons.Rounded.AddAlert, contentDescription = "alert")
                            Text("添加提醒", modifier = Modifier.padding(start = 6.dp))
                        }
                    }
                }

                if (state.loading) {
                    ListSkeleton(rows = 3)
                }

                state.quote?.let { quote ->
                    MotionReveal(delayMs = 150) {
                        QuoteOverviewCard(quote = quote)
                    }

                    if (state.kline.isNotEmpty()) {
                        MotionReveal(delayMs = 180) {
                            KlineCard(candles = state.kline)
                        }
                    }
                }

                state.shortPred?.let { pred ->
                    MotionReveal(delayMs = 220) {
                        PredictionCard(title = "量化预测 (短期 1-7天)", prediction = pred)
                    }
                }

                if (shortAi != null) {
                    MotionReveal(delayMs = 250) {
                        AiJudgementCard(title = "AI第二意见 (短期)", judgement = shortAi)
                    }
                } else if (!state.loading) {
                    MotionReveal(delayMs = 250) {
                        AiUnavailableCard(title = "AI第二意见 (短期)")
                    }
                }

                state.midPred?.let { pred ->
                    MotionReveal(delayMs = 280) {
                        PredictionCard(title = "量化预测 (中期 1-3月)", prediction = pred)
                    }
                }

                if (midAi != null) {
                    MotionReveal(delayMs = 310) {
                        AiJudgementCard(title = "AI第二意见 (中期)", judgement = midAi)
                    }
                } else if (!state.loading) {
                    MotionReveal(delayMs = 310) {
                        AiUnavailableCard(title = "AI第二意见 (中期)")
                    }
                }

                state.explain?.let {
                    MotionReveal(delayMs = 340) {
                        Card(
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
                        ) {
                            Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text("预测依据", style = MaterialTheme.typography.titleMedium)
                                Text(
                                    "依据新鲜度: ${freshnessText(it.dataFreshness)}",
                                    color = freshnessColor(it.dataFreshness),
                                )
                                Text("短期置信区间: ${signedPercent(it.confidenceIntervalPct.first)} ~ ${signedPercent(it.confidenceIntervalPct.second)}")
                                Text("核心因子贡献")
                                it.topFactors.forEach { factor ->
                                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                        Text(factor.name)
                                        Text(
                                            text = String.format("%.2f", factor.contribution),
                                            color = numberColor(factor.contribution),
                                        )
                                    }
                                }
                                if (it.riskFlags.isNotEmpty()) {
                                    Text("风险标签")
                                    it.riskFlags.forEach { flag ->
                                        Text("• $flag", color = riskFlagColor(flag))
                                    }
                                }
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    OutlinedButton(onClick = { viewModel.submitFeedback(code, "short", true) }) {
                                        Text("有帮助")
                                    }
                                    OutlinedButton(
                                        onClick = { viewModel.submitFeedback(code, "short", false) },
                                        colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.onSurfaceVariant),
                                    ) {
                                        Text("需改进")
                                    }
                                }
                            }
                        }
                    }
                }

                state.notice?.let { Text(it, color = Color(0xFF0B8A43)) }
                state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@Composable
private fun OverviewSignalCard(
    shortPred: Prediction?,
    midPred: Prediction?,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF123E6C)),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Icon(Icons.AutoMirrored.Rounded.TrendingUp, contentDescription = "signal", tint = Color.White)
                Text("综合信号总览", style = MaterialTheme.typography.titleMedium, color = Color.White)
            }
            Text(
                shortPred?.let { "短期上涨概率 ${(it.upProbability * 100).toInt()}%，预期 ${signedPercent(it.expectedReturnPct)}" }
                    ?: "短期信号生成中",
                color = Color.White.copy(alpha = 0.92f),
            )
            Text(
                midPred?.let { "中期上涨概率 ${(it.upProbability * 100).toInt()}%，预期 ${signedPercent(it.expectedReturnPct)}" }
                    ?: "中期信号生成中",
                color = Color.White.copy(alpha = 0.9f),
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Rounded.NotificationsActive, contentDescription = "notify", tint = Color(0xFFA9D5FF))
                Text(
                    "可添加提醒阈值进行跟踪",
                    modifier = Modifier.padding(start = 6.dp),
                    color = Color.White.copy(alpha = 0.88f),
                )
            }
        }
    }
}

@Composable
private fun QuoteOverviewCard(quote: Quote) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("基础行情", style = MaterialTheme.typography.titleMedium)
                FreshnessPill(value = freshnessText(quote.dataFreshness), color = freshnessColor(quote.dataFreshness))
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "净值",
                    value = String.format("%.3f", quote.nav),
                    valueColor = MaterialTheme.colorScheme.onSurface,
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "当日涨跌",
                    value = signedPercent(quote.dailyChangePct),
                    valueColor = numberColor(quote.dailyChangePct),
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "20日波动",
                    value = "${String.format("%.2f", quote.volatility20d)}%",
                    valueColor = Color(0xFFB26A00),
                )
            }

            Text(
                "数据时间：${formatAsOf(quote.asOf)}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun MetricTile(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    valueColor: Color,
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF3F7FD)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(3.dp),
        ) {
            Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.titleSmall, color = valueColor)
        }
    }
}

@Composable
private fun FreshnessPill(value: String, color: Color) {
    Box(
        modifier = Modifier
            .background(color = color.copy(alpha = 0.16f), shape = MaterialTheme.shapes.small)
            .padding(horizontal = 10.dp, vertical = 5.dp),
    ) {
        Text(value, style = MaterialTheme.typography.labelMedium, color = color)
    }
}

@Composable
private fun PredictionCard(title: String, prediction: Prediction) {
    val upProgress by animateFloatAsState(
        targetValue = prediction.upProbability.toFloat(),
        animationSpec = tween(durationMillis = 900),
        label = "up_progress",
    )
    val confidenceProgress by animateFloatAsState(
        targetValue = prediction.confidence.toFloat(),
        animationSpec = tween(durationMillis = 900),
        label = "confidence_progress",
    )

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF7FBFF)),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text("数据时间: ${formatAsOf(prediction.asOf)}")
            Text(
                "新鲜度: ${freshnessText(prediction.dataFreshness)}",
                color = freshnessColor(prediction.dataFreshness),
            )
            Text("上涨概率: ${(prediction.upProbability * 100).toInt()}%")
            LinearProgressIndicator(
                progress = { upProgress },
                modifier = Modifier.fillMaxWidth(),
                color = Color(0xFF0C5B9F),
            )
            Text("预期涨幅: ${signedPercent(prediction.expectedReturnPct)}", color = numberColor(prediction.expectedReturnPct))
            Text("置信度: ${(prediction.confidence * 100).toInt()}%")
            LinearProgressIndicator(
                progress = { confidenceProgress },
                modifier = Modifier.fillMaxWidth(),
                color = Color(0xFF126A57),
            )
        }
    }
}

@Composable
private fun AiJudgementCard(title: String, judgement: AiJudgement) {
    val adjustedProgress by animateFloatAsState(
        targetValue = judgement.adjustedUpProbability.toFloat(),
        animationSpec = tween(durationMillis = 900),
        label = "adjusted_up_progress",
    )

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFEFF5FF)),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text("数据时间: ${formatAsOf(judgement.asOf)}")
            Text(
                "新鲜度: ${freshnessText(judgement.dataFreshness)}",
                color = freshnessColor(judgement.dataFreshness),
            )
            Text(
                "趋势判断: ${trendText(judgement.trend)} (${judgement.trendStrength}分)",
                color = trendColor(judgement.trend),
            )
            Text("与量化一致性: ${agreementText(judgement.agreementWithModel)}")
            Text("AI调整后上涨概率: ${(judgement.adjustedUpProbability * 100).toInt()}%")
            LinearProgressIndicator(
                progress = { adjustedProgress },
                modifier = Modifier.fillMaxWidth(),
                color = Color(0xFF1E5EFF),
            )
            Text(
                "置信修正: ${if (judgement.confidenceAdjustment >= 0) "+" else ""}${String.format("%.2f", judgement.confidenceAdjustment)}",
                color = numberColor(judgement.confidenceAdjustment),
            )
            Text("依据来源: ${judgement.provider}/${judgement.model}")
            Text("关键依据")
            judgement.keyReasons.forEach { Text("• $it") }
            if (judgement.riskWarnings.isNotEmpty()) {
                Text("风险提示")
                judgement.riskWarnings.forEach { Text("• $it", color = Color(0xFFC62828)) }
            }
            Text(judgement.summary, color = Color(0xFF2D3A4A))
        }
    }
}

@Composable
private fun AiUnavailableCard(title: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF1F3F6))
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text("AI第二意见暂不可用，当前展示量化预测结果。", color = Color(0xFF666666))
        }
    }
}

@Composable
private fun KlineCard(candles: List<KlineCandle>) {
    val axisColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.35f)
    val bullish = Color(0xFF0B8A43)
    val bearish = Color(0xFFC62828)

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("净值趋势图（近60日）", style = MaterialTheme.typography.titleMedium)
            Text("由净值序列估算生成，仅用于趋势参考（非真实OHLC K线）")
            Canvas(modifier = Modifier.fillMaxWidth().height(120.dp)) {
                val min = candles.minOfOrNull { it.low } ?: 0.0
                val max = candles.maxOfOrNull { it.high } ?: 1.0
                val range = (max - min).takeIf { it > 0 } ?: 1.0
                val bodyWidth = (size.width / candles.size * 0.55f).coerceAtLeast(2f)
                val stepX = if (candles.size > 1) size.width / (candles.size - 1) else size.width

                candles.forEachIndexed { idx, c ->
                    val x = idx * stepX
                    val highY = ((max - c.high) / range * size.height).toFloat()
                    val lowY = ((max - c.low) / range * size.height).toFloat()
                    val openY = ((max - c.open) / range * size.height).toFloat()
                    val closeY = ((max - c.close) / range * size.height).toFloat()
                    val up = c.close >= c.open
                    val color = if (up) bullish else bearish

                    drawLine(
                        color = color,
                        start = Offset(x, highY),
                        end = Offset(x, lowY),
                        strokeWidth = 2f,
                    )

                    val top = minOf(openY, closeY)
                    val bottom = maxOf(openY, closeY)
                    val bodyHeight = (bottom - top).coerceAtLeast(2f)
                    drawRect(
                        color = color,
                        topLeft = Offset(x - bodyWidth / 2f, top),
                        size = Size(bodyWidth, bodyHeight),
                    )
                }

                drawLine(
                    color = axisColor,
                    start = Offset(0f, size.height - 2f),
                    end = Offset(size.width, size.height - 2f),
                    strokeWidth = 2f,
                )
            }
        }
    }
}

private fun signedPercent(v: Double): String {
    return if (v > 0) "+${String.format("%.2f", v)}%" else "${String.format("%.2f", v)}%"
}

private fun formatAsOf(raw: String): String {
    val outputFmt = DateTimeFormatter.ofPattern("MM-dd HH:mm")
    return runCatching {
        OffsetDateTime.parse(raw).format(outputFmt)
    }.recoverCatching {
        LocalDateTime.parse(raw).format(outputFmt)
    }.getOrElse { raw }
}

private fun freshnessText(value: String): String {
    return when (value.lowercase()) {
        "fresh" -> "新鲜"
        "lagging" -> "一般"
        "stale" -> "过期"
        else -> "未知"
    }
}

private fun freshnessColor(value: String): Color {
    return when (value.lowercase()) {
        "fresh" -> Color(0xFF0B8A43)
        "lagging" -> Color(0xFFB26A00)
        "stale" -> Color(0xFFC62828)
        else -> Color(0xFF666666)
    }
}

private fun riskFlagColor(flag: String): Color {
    return if (flag == "风险整体可控") Color(0xFF0B8A43) else Color(0xFFC62828)
}

private fun trendText(value: String): String {
    return when (value.lowercase()) {
        "up" -> "看涨"
        "down" -> "看跌"
        "sideways" -> "震荡"
        else -> "未知"
    }
}

private fun trendColor(value: String): Color {
    return when (value.lowercase()) {
        "up" -> Color(0xFF0B8A43)
        "down" -> Color(0xFFC62828)
        "sideways" -> Color(0xFFB26A00)
        else -> Color(0xFF666666)
    }
}

private fun agreementText(value: String): String {
    return when (value.lowercase()) {
        "agree" -> "一致"
        "partial" -> "部分一致"
        "disagree" -> "不一致"
        else -> "未知"
    }
}

@Composable
private fun numberColor(v: Double): Color {
    return when {
        v > 0 -> Color(0xFF0B8A43)
        v < 0 -> Color(0xFFC62828)
        else -> MaterialTheme.colorScheme.onSurface
    }
}
