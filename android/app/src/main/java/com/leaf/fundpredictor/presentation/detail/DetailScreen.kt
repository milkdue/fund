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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.presentation.components.ListSkeleton

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
                    }
                }

                if (state.shortPred != null && state.midPred != null) {
                    TrendPreviewCard(
                        nav = quote.nav,
                        shortExpected = state.shortPred!!.expectedReturnPct,
                        midExpected = state.midPred!!.expectedReturnPct,
                    )
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
                        Text("解释因子", style = MaterialTheme.typography.titleMedium)
                        Text("区间: ${signedPercent(it.confidenceIntervalPct.first)} ~ ${signedPercent(it.confidenceIntervalPct.second)}")
                        it.topFactors.forEach { factor ->
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(factor.name)
                                Text(
                                    text = String.format("%.2f", factor.contribution),
                                    color = numberColor(factor.contribution),
                                )
                            }
                        }
                    }
                }
            }

            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        }
    }
}

@Composable
private fun PredictionCard(title: String, prediction: Prediction) {
    Card {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
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
private fun TrendPreviewCard(nav: Double, shortExpected: Double, midExpected: Double) {
    val points = buildTrendPreview(nav, shortExpected, midExpected)
    val trendColor = if (points.last() >= points.first()) Color(0xFF0B8A43) else Color(0xFFC62828)
    val axisColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.35f)

    Card {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("趋势预览 (模拟)", style = MaterialTheme.typography.titleMedium)
            Text("基于当前净值与短/中期预测，生成未来路径参考")
            Canvas(modifier = Modifier.fillMaxWidth().height(120.dp)) {
                val min = points.minOrNull() ?: 0.0
                val max = points.maxOrNull() ?: 1.0
                val range = (max - min).takeIf { it > 0 } ?: 1.0
                val stepX = size.width / (points.size - 1)
                val offsets = points.mapIndexed { idx, v ->
                    val x = idx * stepX
                    val y = ((max - v) / range * size.height).toFloat()
                    Offset(x = x, y = y)
                }
                for (i in 1 until offsets.size) {
                    drawLine(
                        color = trendColor,
                        start = offsets[i - 1],
                        end = offsets[i],
                        strokeWidth = 6f,
                        cap = StrokeCap.Round,
                    )
                }
                drawLine(
                    color = axisColor,
                    start = Offset(0f, size.height - 2f),
                    end = Offset(size.width, size.height - 2f),
                    strokeWidth = 2f,
                    cap = StrokeCap.Round,
                )
                drawCircle(color = trendColor, radius = 6f, center = offsets.last(), style = Stroke(width = 4f))
            }
        }
    }
}

private fun buildTrendPreview(nav: Double, shortExpected: Double, midExpected: Double): List<Double> {
    val p0 = nav
    val p1 = p0 * (1.0 + shortExpected / 100.0 * 0.25)
    val p2 = p0 * (1.0 + shortExpected / 100.0 * 0.55)
    val p3 = p0 * (1.0 + shortExpected / 100.0 * 0.85)
    val p4 = p0 * (1.0 + midExpected / 100.0 * 0.30)
    val p5 = p0 * (1.0 + midExpected / 100.0 * 0.60)
    val p6 = p0 * (1.0 + midExpected / 100.0 * 0.85)
    val p7 = p0 * (1.0 + midExpected / 100.0)
    return listOf(p0, p1, p2, p3, p4, p5, p6, p7)
}

private fun signedPercent(v: Double): String {
    return if (v > 0) "+${String.format("%.2f", v)}%" else "${String.format("%.2f", v)}%"
}

@Composable
private fun numberColor(v: Double): Color {
    return when {
        v > 0 -> Color(0xFF0B8A43)
        v < 0 -> Color(0xFFC62828)
        else -> MaterialTheme.colorScheme.onSurface
    }
}
