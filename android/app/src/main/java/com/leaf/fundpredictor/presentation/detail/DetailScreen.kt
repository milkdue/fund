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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.Article
import androidx.compose.material.icons.automirrored.rounded.TrendingUp
import androidx.compose.material.icons.rounded.AddAlert
import androidx.compose.material.icons.rounded.NotificationsActive
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.AiJudgement
import com.leaf.fundpredictor.domain.model.Estimate
import com.leaf.fundpredictor.domain.model.KlineCandle
import com.leaf.fundpredictor.domain.model.NewsSignal
import com.leaf.fundpredictor.domain.model.Prediction
import com.leaf.fundpredictor.domain.model.PredictionChange
import com.leaf.fundpredictor.domain.model.Quote
import com.leaf.fundpredictor.domain.model.ScoreComponent
import com.leaf.fundpredictor.presentation.components.LabelWithTooltip
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
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(code) { viewModel.load(code) }
    LaunchedEffect(state.notice) {
        val message = state.notice ?: return@LaunchedEffect
        snackbarHostState.showSnackbar(message)
        viewModel.consumeNotice()
    }
    LaunchedEffect(state.error) {
        val message = state.error ?: return@LaunchedEffect
        snackbarHostState.showSnackbar(message)
        viewModel.consumeError()
    }

    Scaffold(
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) },
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
                actions = {
                    IconButton(
                        enabled = !state.loading && !state.refreshing,
                        onClick = { viewModel.refresh(code) },
                    ) {
                        if (state.refreshing) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.primary,
                            )
                        } else {
                            Icon(Icons.Rounded.Refresh, contentDescription = "refresh")
                        }
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
                if (state.refreshing) {
                    MotionReveal(delayMs = 10) {
                        Card(
                            colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F3FF)),
                            elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                        ) {
                            Text(
                                "正在刷新最新数据，当前内容已保留。",
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                                color = Color(0xFF0C5B9F),
                            )
                        }
                    }
                }

                state.lastRefreshedAt?.let { refreshedAt ->
                    MotionReveal(delayMs = 24) {
                        RefreshStatusCard(
                            refreshedAt = refreshedAt,
                            summary = state.refreshSummary,
                            details = state.refreshDetails,
                        )
                    }
                }

                MotionReveal(delayMs = 40) {
                    OverviewSignalCard(
                        shortPred = state.shortPred,
                        midPred = state.midPred,
                    )
                }

                if (!state.loading) {
                    MotionReveal(delayMs = 75) {
                        DecisionHintCard(
                            quote = state.quote,
                            estimate = state.estimate,
                            shortPred = state.shortPred,
                            newsSignal = state.newsSignal,
                        )
                    }
                }

                if (!state.loading) {
                    MotionReveal(delayMs = 110) {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                            FilledTonalButton(
                                modifier = Modifier.weight(1f),
                                enabled = !state.isAddingWatchlist && !state.isSettingAlert && !state.isWatchlisted,
                                onClick = { viewModel.addWatchlist(code) },
                            ) {
                                if (state.isAddingWatchlist) {
                                    CircularProgressIndicator(
                                        modifier = Modifier
                                            .size(16.dp)
                                            .padding(end = 6.dp),
                                        strokeWidth = 2.dp,
                                        color = MaterialTheme.colorScheme.primary,
                                    )
                                    Text("添加中...")
                                } else if (state.isWatchlisted) {
                                    Icon(Icons.Rounded.Star, contentDescription = "watch")
                                    Text("已加入自选", modifier = Modifier.padding(start = 6.dp))
                                } else {
                                    Icon(Icons.Rounded.Star, contentDescription = "watch")
                                    Text("加入自选", modifier = Modifier.padding(start = 6.dp))
                                }
                            }
                            OutlinedButton(
                                modifier = Modifier.weight(1f),
                                enabled = !state.isAddingWatchlist && !state.isSettingAlert && !state.hasAlertConfigured,
                                onClick = { viewModel.setDefaultAlert(code) },
                            ) {
                                if (state.isSettingAlert) {
                                    CircularProgressIndicator(
                                        modifier = Modifier
                                            .size(16.dp)
                                            .padding(end = 6.dp),
                                        strokeWidth = 2.dp,
                                        color = MaterialTheme.colorScheme.primary,
                                    )
                                    Text("设置中...")
                                } else if (state.hasAlertConfigured) {
                                    Icon(Icons.Rounded.NotificationsActive, contentDescription = "alert")
                                    Text("已添加提醒", modifier = Modifier.padding(start = 6.dp))
                                } else {
                                    Icon(Icons.Rounded.AddAlert, contentDescription = "alert")
                                    Text("添加提醒", modifier = Modifier.padding(start = 6.dp))
                                }
                            }
                        }
                    }
                }

                if (state.loading) {
                    ListSkeleton(rows = 3)
                }

                state.quote?.let { quote ->
                    MotionReveal(delayMs = 150) {
                        QuoteOverviewCard(
                            quote = quote,
                            estimate = state.estimate,
                        )
                    }

                    if (state.kline.isNotEmpty()) {
                        MotionReveal(delayMs = 180) {
                            KlineCard(candles = state.kline)
                        }
                    }
                }

                state.newsSignal?.let { signal ->
                    MotionReveal(delayMs = 205) {
                        NewsSignalCard(signal = signal)
                    }
                }

                state.shortPred?.let { pred ->
                    MotionReveal(delayMs = 220) {
                        PredictionCard(title = "量化预测 (短期 1-7天)", prediction = pred)
                    }
                }

                state.shortChange?.let { change ->
                    MotionReveal(delayMs = 235) {
                        PredictionChangeCard(change = change)
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
                                        FactorLabel(name = factor.name)
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

            }
        }
    }
}

@Composable
private fun RefreshStatusCard(
    refreshedAt: String,
    summary: String?,
    details: List<String>,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF8FBFF)),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                "上次刷新：$refreshedAt",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            summary?.takeIf { it.isNotBlank() }?.let {
                Text(
                    it,
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF0C5B9F),
                )
            }
            details.forEach { line ->
                Text(
                    "• $line",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
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
                shortPred?.let {
                    "短期 ${it.scorecard.actionLabel} · 综合 ${it.scorecard.totalScore} · 预期 ${signedPercent(it.expectedReturnPct)}"
                }
                    ?: "短期信号生成中",
                color = Color.White.copy(alpha = 0.92f),
            )
            Text(
                midPred?.let {
                    "中期 ${it.scorecard.actionLabel} · 综合 ${it.scorecard.totalScore} · 预期 ${signedPercent(it.expectedReturnPct)}"
                }
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
private fun QuoteOverviewCard(
    quote: Quote,
    estimate: Estimate?,
) {
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
                Text("正式净值", style = MaterialTheme.typography.titleMedium)
                FreshnessPill(value = freshnessText(quote.dataFreshness), color = freshnessColor(quote.dataFreshness))
            }
            LabelWithTooltip(
                label = quote.sourceLabel,
                tooltip = buildString {
                    append("这是当前预测主链路使用的正式净值来源。")
                    if (quote.qualityFlags.isNotEmpty()) {
                        append(" 当前检测到：")
                        append(quote.qualityFlags.joinToString("、"))
                    } else {
                        append(" 当前数据质量正常。")
                    }
                },
                labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
            )

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
            if (quote.qualityFlags.isNotEmpty()) {
                QualityFlagBlock(
                    title = "正式净值提示",
                    flags = quote.qualityFlags,
                    tooltip = "质量提示用于提醒你当前数据是否存在延迟、异常波动或与上一净值不一致的情况。",
                )
            }
            estimate?.let {
                EstimateCard(estimate = it)
            }
        }
    }
}

@Composable
private fun EstimateCard(estimate: Estimate) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF8FBFF)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("盘中估值参考", style = MaterialTheme.typography.titleSmall)
                FreshnessPill(value = freshnessText(estimate.dataFreshness), color = freshnessColor(estimate.dataFreshness))
            }
            LabelWithTooltip(
                label = estimate.sourceLabel,
                tooltip = "盘中估值只适合作为参考，不等于基金公司最终确认的正式净值。",
                labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "估算净值",
                    value = String.format("%.3f", estimate.estimateNav),
                    valueColor = MaterialTheme.colorScheme.onSurface,
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "估算涨跌",
                    value = signedPercent(estimate.estimateChangePct),
                    valueColor = numberColor(estimate.estimateChangePct),
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "相对正式净值",
                    value = estimate.referenceNav?.takeIf { it != 0.0 }?.let { ref ->
                        signedPercent((estimate.estimateNav - ref) / ref * 100)
                    } ?: "--",
                    valueColor = estimate.referenceNav?.takeIf { it != 0.0 }?.let { ref ->
                        numberColor((estimate.estimateNav - ref) / ref * 100)
                    } ?: MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                "估值时间：${formatAsOf(estimate.asOf)}" +
                    (estimate.referenceNavAsOf?.let { " · 对比净值：${formatAsOf(it)}" } ?: ""),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (estimate.qualityFlags.isNotEmpty()) {
                QualityFlagBlock(
                    title = "盘中估值提示",
                    flags = estimate.qualityFlags,
                    tooltip = "当盘中估值更新变慢，或与最近正式净值偏离过大时，会在这里提示你不要过度依赖盘中数值。",
                )
            }
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
private fun QualityFlagBlock(
    title: String,
    flags: List<String>,
    tooltip: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        LabelWithTooltip(
            label = title,
            tooltip = tooltip,
            labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        flags.forEach { flag ->
            Text(
                text = "• $flag",
                style = MaterialTheme.typography.bodySmall,
                color = riskFlagColor(flag),
            )
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
private fun NewsSignalCard(signal: NewsSignal) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Icon(Icons.AutoMirrored.Rounded.Article, contentDescription = "news", tint = MaterialTheme.colorScheme.primary)
                Text("公告与舆情", style = MaterialTheme.typography.titleMedium)
            }
            Text(
                "最近交易日：${signal.tradeDate}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "样本数",
                    value = "${signal.headlineCount}",
                    valueColor = MaterialTheme.colorScheme.onSurface,
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "影响强度",
                    value = newsImpactStrengthText(signal.impactStrength),
                    valueColor = newsImpactColor(signal.impactStrength),
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "最近事件",
                    value = newsAgeText(signal.latestAgeDays),
                    valueColor = newsImpactColor(signal.impactStrength),
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "情绪分",
                    value = String.format("%.2f", signal.sentimentScore),
                    valueColor = numberColor(signal.sentimentScore),
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "事件分",
                    value = String.format("%.2f", signal.eventScore),
                    valueColor = numberColor(signal.eventScore),
                )
                MetricTile(
                    modifier = Modifier.weight(1f),
                    label = "热度变化",
                    value = String.format("%.2f", signal.volumeShock),
                    valueColor = numberColor(signal.volumeShock),
                )
            }
            signal.latestPublishedAt?.let {
                Text(
                    "最新事件时间：${formatAsOf(it)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (signal.impactSummary.isNotBlank()) {
                Text(
                    signal.impactSummary,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            LabelWithTooltip(
                label = "代表性事件",
                tooltip = "这一栏会显示当前被系统抽样为最有代表性的公告或外部舆情标题，帮助你判断最近到底发生了什么。",
                labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                if (signal.sampleTitle.isBlank()) "暂无可展示样本" else signal.sampleTitle,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                newsImpactReading(signal),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun DecisionHintCard(
    quote: Quote?,
    estimate: Estimate?,
    shortPred: Prediction?,
    newsSignal: NewsSignal?,
) {
    val prediction = shortPred ?: return
    val headline = when (prediction.scorecard.actionLabel) {
        "强关注" -> "当前可优先跟踪"
        "关注" -> "当前可继续跟踪"
        "观察" -> "当前更适合观察等待"
        "回避" -> "当前不宜激进操作"
        else -> "当前建议继续观察"
    }
    val suggestions = buildList {
        add(signalBiasSummary(prediction.scorecard.signalBias, prediction.horizon, prediction.expectedReturnPct))
        quote?.let {
            add(
                when (it.dataFreshness.lowercase()) {
                    "fresh" -> "正式净值是最新一轮，可作为主判断依据。"
                    "lagging" -> "正式净值略有延迟，方向可参考，但不适合过度精细择时。"
                    else -> "正式净值已过期，当前判断要降低信心。"
                }
            )
        }
        estimate?.referenceNav?.takeIf { it != 0.0 }?.let { ref ->
            val driftPct = (estimate.estimateNav - ref) / ref * 100
            add(
                when {
                    kotlin.math.abs(driftPct) >= 1.0 -> "盘中估值相对正式净值偏离 ${signedPercent(driftPct)}，盘中波动较明显。"
                    kotlin.math.abs(driftPct) >= 0.35 -> "盘中估值相对正式净值偏离 ${signedPercent(driftPct)}，可继续观察盘中方向是否延续。"
                    else -> "盘中估值与正式净值差异不大，日内情绪暂未明显偏离。"
                }
            )
        }
        newsSignal?.let {
            add(
                when (it.impactStrength.lowercase()) {
                    "strong" -> "最近舆情影响较强，需要把事件催化一起纳入判断。"
                    "medium" -> "最近有一定事件影响，但还不足以单独决定方向。"
                    "weak" -> "最近舆情影响较弱，主判断仍应回到净值趋势和市场环境。"
                    else -> "当前缺少足够的新事件样本，舆情项按中性看待。"
                }
            )
        }
    }.take(4)

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF8FBFF)),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("当前判断提示", style = MaterialTheme.typography.titleMedium)
            Text(
                headline,
                style = MaterialTheme.typography.titleSmall,
                color = actionColor(prediction.scorecard.actionLabel),
            )
            suggestions.forEach { tip ->
                Text(
                    text = "• $tip",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
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
    var showScoreSheet by remember { mutableStateOf(false) }

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
            Text("模型: ${prediction.modelVersion} · 来源: ${prediction.dataSource}")
            prediction.snapshotId?.let { snapshot ->
                Text("快照编号: $snapshot", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
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
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                ScorePill(
                    modifier = Modifier.weight(1f),
                    label = "综合评分",
                    value = "${prediction.scorecard.totalScore}",
                    color = actionColor(prediction.scorecard.actionLabel),
                    tooltip = prediction.scorecard.summary,
                )
                ScorePill(
                    modifier = Modifier.weight(1f),
                    label = "风险分",
                    value = "${prediction.scorecard.riskScore}",
                    color = riskScoreColor(prediction.scorecard.riskScore),
                    tooltip = "风险分越高，代表波动、数据质量和模型分歧带来的风险越低。当前风险分 ${prediction.scorecard.riskScore}。",
                )
                ScorePill(
                    modifier = Modifier.weight(1f),
                    label = "行动标签",
                    value = prediction.scorecard.actionLabel,
                    color = actionColor(prediction.scorecard.actionLabel),
                    tooltip = actionLabelTooltip(prediction.scorecard.actionLabel),
                )
            }
            Text(
                "方向结论：${signalBiasSummary(prediction.scorecard.signalBias, prediction.horizon, prediction.expectedReturnPct)}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                prediction.scorecard.summary,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            TextButton(
                onClick = { showScoreSheet = true },
                modifier = Modifier.align(Alignment.End),
            ) {
                Text("查看评分依据")
            }
            if (prediction.scorecard.components.isNotEmpty()) {
                Text("评分拆解", style = MaterialTheme.typography.titleSmall)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    prediction.scorecard.components.take(3).forEach { component ->
                        ScorePill(
                            modifier = Modifier.weight(1f),
                            label = component.label,
                            value = "${component.score}",
                            color = componentColor(component.score),
                            tooltip = component.summary,
                        )
                    }
                }
                prediction.scorecard.components.drop(3).take(3).takeIf { it.isNotEmpty() }?.let { tail ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        tail.forEach { component ->
                            ScorePill(
                                modifier = Modifier.weight(1f),
                                label = component.label,
                                value = "${component.score}",
                                color = componentColor(component.score),
                                tooltip = component.summary,
                            )
                        }
                        repeat((3 - tail.size).coerceAtLeast(0)) {
                            Box(modifier = Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }

    if (showScoreSheet) {
        ScoreExplanationSheet(
            title = title,
            prediction = prediction,
            onDismiss = { showScoreSheet = false },
        )
    }
}

@Composable
private fun PredictionChangeCard(change: PredictionChange) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF8EC)),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("预测变化依据（相对上次）", style = MaterialTheme.typography.titleMedium)
            Text(
                "新鲜度: ${freshnessText(change.dataFreshness)}",
                color = freshnessColor(change.dataFreshness),
            )
            Text(change.summary)

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MetricDeltaTile(
                    modifier = Modifier.weight(1f),
                    label = "概率变化",
                    value = signedDelta(change.upProbabilityDelta * 100),
                    valueColor = numberColor(change.upProbabilityDelta),
                )
                MetricDeltaTile(
                    modifier = Modifier.weight(1f),
                    label = "预期变化",
                    value = signedDelta(change.expectedReturnPctDelta),
                    valueColor = numberColor(change.expectedReturnPctDelta),
                    suffix = "%",
                )
                MetricDeltaTile(
                    modifier = Modifier.weight(1f),
                    label = "置信变化",
                    value = signedDelta(change.confidenceDelta * 100),
                    valueColor = numberColor(change.confidenceDelta),
                    suffix = "百分点",
                )
            }

            if (change.changedFactors.isNotEmpty()) {
                Text("主要因子变化", style = MaterialTheme.typography.titleSmall)
                change.changedFactors.take(5).forEach { factor ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        FactorLabel(
                            name = factor.name,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(
                            "${signedDelta(factor.delta)}",
                            color = numberColor(factor.delta),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun MetricDeltaTile(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    valueColor: Color,
    suffix: String = "%",
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFFBF2)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("$value$suffix", style = MaterialTheme.typography.titleSmall, color = valueColor)
        }
    }
}

@Composable
private fun ScorePill(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    color: Color,
    tooltip: String? = null,
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.12f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            if (tooltip.isNullOrBlank()) {
                Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            } else {
                LabelWithTooltip(
                    label = label,
                    tooltip = tooltip,
                    labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(value, style = MaterialTheme.typography.titleSmall, color = color)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ScoreExplanationSheet(
    title: String,
    prediction: Prediction,
    onDismiss: () -> Unit,
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFFF9FBFF),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleLarge)
            Text(
                "${prediction.scorecard.actionLabel} · 综合 ${prediction.scorecard.totalScore} · 风险 ${prediction.scorecard.riskScore}",
                style = MaterialTheme.typography.titleSmall,
                color = actionColor(prediction.scorecard.actionLabel),
            )
            Text(
                prediction.scorecard.summary,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            prediction.scorecard.components.forEach { component ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 10.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            LabelWithTooltip(
                                label = component.label,
                                tooltip = component.summary,
                            )
                            Text(
                                "${component.score}",
                                style = MaterialTheme.typography.titleMedium,
                                color = componentColor(component.score),
                            )
                        }
                        Text(
                            component.summary,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        ScoreDetailLines(component)
                    }
                }
            }
            Box(modifier = Modifier.padding(bottom = 18.dp))
        }
    }
}

@Composable
private fun ScoreDetailLines(component: ScoreComponent) {
    if (component.detailLines.isEmpty()) return
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        component.detailLines.forEach { line ->
            Text(
                "• $line",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

private fun signalBiasSummary(bias: String, horizon: String, expectedReturnPct: Double): String {
    val window = if (horizon == "short") "未来1-7天" else "未来1-3个月"
    return when (bias) {
        "偏多" -> if (expectedReturnPct >= 2.5) "${window}更偏向上行，趋势相对明确" else "${window}略偏上行，但还不是强趋势"
        "偏空" -> if (expectedReturnPct <= -1.0) "${window}更偏向回落，建议先控制风险" else "${window}略偏下行，先以观察为主"
        else -> if (expectedReturnPct >= 0) "${window}大概率震荡，略偏上行" else "${window}大概率震荡，略偏下行"
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
            LabelWithTooltip(
                label = title,
                tooltip = "AI 指人工智能。这里是结合量化结果、市场环境和文本信息后的辅助判断，不是保证收益的结论。",
            )
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
            LabelWithTooltip(
                label = title,
                tooltip = "AI 指人工智能。当前没有可用的 AI 辅助判断，所以先展示量化预测结果。",
            )
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
            LabelWithTooltip(
                label = "净值趋势图（近60日）",
                tooltip = "K线是把一段时间内的开盘、最高、最低、收盘画成柱状图，用来看趋势和波动。",
            )
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text("由净值序列估算生成，仅用于趋势参考（非真实 OHLC K 线）")
                LabelWithTooltip(
                    label = "OHLC",
                    tooltip = "OHLC 分别是开盘价、最高价、最低价、收盘价。",
                    labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
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

private fun signedDelta(v: Double): String {
    return if (v > 0) "+${String.format("%.2f", v)}" else String.format("%.2f", v)
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

private fun actionColor(label: String): Color {
    return when (label) {
        "强关注" -> Color(0xFF0B8A43)
        "关注" -> Color(0xFF126A57)
        "观察" -> Color(0xFFB26A00)
        "回避" -> Color(0xFFC62828)
        else -> Color(0xFF596072)
    }
}

private fun actionLabelTooltip(label: String): String {
    return when (label) {
        "强关注" -> "强关注表示方向、空间和风险控制三项同时较优，可以优先放进观察列表。"
        "关注" -> "关注表示信号整体较好，但还没有到最强区间。"
        "观察" -> "观察表示当前有部分积极因素，但还不足以支持更积极动作。"
        "回避" -> "回避表示风险、分歧或预期收益不够理想，当前更适合少动。"
        else -> "行动标签用于把复杂评分结果压缩成更容易理解的结论。"
    }
}

private fun riskScoreColor(score: Int): Color {
    return when {
        score >= 70 -> Color(0xFF0B8A43)
        score >= 45 -> Color(0xFFB26A00)
        else -> Color(0xFFC62828)
    }
}

private fun componentColor(score: Int): Color {
    return when {
        score >= 75 -> Color(0xFF0B8A43)
        score >= 55 -> Color(0xFF0C5B9F)
        score >= 40 -> Color(0xFFB26A00)
        else -> Color(0xFFC62828)
    }
}

private fun newsImpactStrengthText(value: String): String {
    return when (value.lowercase()) {
        "strong" -> "强"
        "medium" -> "中"
        "weak" -> "弱"
        else -> "中性"
    }
}

private fun newsImpactColor(value: String): Color {
    return when (value.lowercase()) {
        "strong" -> Color(0xFF0B8A43)
        "medium" -> Color(0xFF0C5B9F)
        "weak" -> Color(0xFFB26A00)
        else -> Color(0xFF70757F)
    }
}

private fun newsAgeText(value: Double?): String {
    if (value == null) return "暂无"
    return when {
        value < 1.0 -> "1天内"
        value <= 2.0 -> "2天内"
        else -> "${String.format("%.1f", value)}天"
    }
}

private fun newsImpactReading(signal: NewsSignal): String {
    if (signal.headlineCount == 0) {
        return "当前没有抓到足够的公告或外部新闻样本，舆情项默认按中性处理。"
    }
    return buildString {
        append(signal.impactSummary.ifBlank { "当前新闻影响暂按中性理解。" })
        append(
            when (signal.impactStrength.lowercase()) {
                "strong" -> " 这类信号更适合作为短期催化一起看。"
                "medium" -> " 这类信号可以辅助判断，但不适合单独决定方向。"
                "weak" -> " 这类信号已经在衰减，主判断仍应看趋势和市场。"
                else -> " 当前仍应以净值趋势和市场环境为主。"
            }
        )
    }
}

@Composable
private fun FactorLabel(
    name: String,
    color: Color = MaterialTheme.colorScheme.onSurface,
) {
    val meaning = factorMeaning(name)
    LabelWithTooltip(
        label = meaning.displayName,
        tooltip = meaning.tooltip,
        labelColor = color,
    )
}

private data class FactorMeaning(
    val displayName: String,
    val tooltip: String,
)

private fun factorMeaning(raw: String): FactorMeaning {
    return when (raw.lowercase()) {
        "style_score" -> FactorMeaning(
            displayName = "风格偏好分",
            tooltip = "style_score：衡量当前市场更偏成长还是偏价值，以及这种风格是否更有利于这只基金。",
        )

        "volatility_20d" -> FactorMeaning(
            displayName = "20日波动率",
            tooltip = "volatility_20d：统计近20个交易日波动有多大。越高代表价格越不稳，风险通常越高。",
        )

        "market_score" -> FactorMeaning(
            displayName = "市场环境分",
            tooltip = "market_score：综合大盘涨跌、动量和波动后的市场风险偏好分数。分数越高，整体环境越偏多。",
        )

        "nav" -> FactorMeaning(
            displayName = "基金净值",
            tooltip = "nav：基金当前单位净值水平。净值本身及其变化会影响趋势判断。",
        )

        "daily_change_pct" -> FactorMeaning(
            displayName = "当日涨跌幅",
            tooltip = "daily_change_pct：最近一个交易日净值的涨跌百分比，用来衡量短期动量。",
        )

        "sentiment_score" -> FactorMeaning(
            displayName = "舆情情绪分",
            tooltip = "sentiment_score：根据公告、新闻和舆情文本得到的情绪强弱分，正值偏利好，负值偏利空。",
        )

        "event_score" -> FactorMeaning(
            displayName = "事件冲击分",
            tooltip = "event_score：重大公告或事件对趋势的短期影响强度，正值偏利好，负值偏利空。",
        )

        "volume_shock_score" -> FactorMeaning(
            displayName = "热度冲击分",
            tooltip = "volume_shock_score：新闻数量和关注度突然变化带来的热度影响，常反映情绪波动。",
        )

        else -> FactorMeaning(
            displayName = raw,
            tooltip = "$raw：这是模型内部使用的特征字段名称，当前暂无中文释义。",
        )
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
