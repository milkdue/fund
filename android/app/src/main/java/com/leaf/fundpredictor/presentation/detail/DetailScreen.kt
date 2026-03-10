package com.leaf.fundpredictor.presentation.detail

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.presentation.components.ListSkeleton
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DetailScreen(code: String, viewModel: DetailViewModel, onBack: () -> Unit) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(code) { viewModel.load(code) }

    Scaffold(topBar = { TopAppBar(title = { Text("基金详情") }) }) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onBack) { Text("返回") }
                Button(onClick = { viewModel.addWatchlist(code) }) { Text("加入自选") }
                Button(onClick = { viewModel.setDefaultAlert(code) }) { Text("添加提醒") }
            }

            Text("基金代码: $code", style = MaterialTheme.typography.titleMedium)

            if (state.loading) {
                ListSkeleton(rows = 3)
            }

            state.quote?.let { quote ->
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                    Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("基础行情", style = MaterialTheme.typography.titleMedium)
                        Text("净值: ${quote.nav}")
                        Text(
                            text = "当日涨跌: ${signedPercent(quote.dailyChangePct)}",
                            color = numberColor(quote.dailyChangePct)
                        )
                        Text("20日波动率: ${quote.volatility20d}%")
                        Text("数据时间: ${formatAsOf(quote.asOf)}")
                        Text(
                            "新鲜度: ${freshnessText(quote.dataFreshness)}",
                            color = freshnessColor(quote.dataFreshness),
                        )
                    }
                }

                if (state.kline.isNotEmpty()) {
                    KlineCard(candles = state.kline)
                }
            }

            state.shortPred?.let { pred ->
                PredictionCard(title = "短期预测 (1-7天)", prediction = pred)
            }

            state.midPred?.let { pred ->
                PredictionCard(title = "中期信号 (1-3月)", prediction = pred)
            }

            state.explain?.let {
                Card {
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
                            Button(onClick = { viewModel.submitFeedback(code, "short", true) }) {
                                Text("有帮助")
                            }
                            Button(onClick = { viewModel.submitFeedback(code, "short", false) }) {
                                Text("没帮助")
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

@Composable
private fun PredictionCard(title: String, prediction: Prediction) {
    Card {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text("数据时间: ${formatAsOf(prediction.asOf)}")
            Text(
                "新鲜度: ${freshnessText(prediction.dataFreshness)}",
                color = freshnessColor(prediction.dataFreshness),
            )
            Text("上涨概率: ${(prediction.upProbability * 100).toInt()}%")
            LinearProgressIndicator(
                progress = { prediction.upProbability.toFloat() },
                modifier = Modifier.fillMaxWidth(),
            )
            Text("预期涨幅: ${signedPercent(prediction.expectedReturnPct)}", color = numberColor(prediction.expectedReturnPct))
            Text("置信度: ${(prediction.confidence * 100).toInt()}%")
            LinearProgressIndicator(
                progress = { prediction.confidence.toFloat() },
                modifier = Modifier.fillMaxWidth(),
                color = MaterialTheme.colorScheme.secondary,
            )
        }
    }
}

@Composable
private fun KlineCard(candles: List<KlineCandle>) {
    val axisColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.35f)
    val bullish = Color(0xFF0B8A43)
    val bearish = Color(0xFFC62828)

    Card {
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

@Composable
private fun numberColor(v: Double): Color {
    return when {
        v > 0 -> Color(0xFF0B8A43)
        v < 0 -> Color(0xFFC62828)
        else -> MaterialTheme.colorScheme.onSurface
    }
}
