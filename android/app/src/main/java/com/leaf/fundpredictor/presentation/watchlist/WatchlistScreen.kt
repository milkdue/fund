package com.leaf.fundpredictor.presentation.watchlist

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.TrendingUp
import androidx.compose.material.icons.rounded.NotificationsActive
import androidx.compose.material.icons.rounded.NotificationsNone
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.WatchlistInsight
import com.leaf.fundpredictor.domain.model.WatchlistItem
import com.leaf.fundpredictor.presentation.components.ListSkeleton
import com.leaf.fundpredictor.presentation.components.MotionReveal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WatchlistScreen(
    viewModel: WatchlistViewModel,
    onBack: () -> Unit,
    onOpenDetail: (String) -> Unit,
) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) { viewModel.load() }

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = { Text("我的自选池") },
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
                        colors = listOf(Color(0xFFECF5FF), Color(0xFFF6FFF9))
                    )
                )
                .padding(innerPadding)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                MotionReveal(delayMs = 40) {
                    OverviewCard(size = maxOf(state.insights.size, state.items.size))
                }

                state.diagnosticsNote?.let { note ->
                    MotionReveal(delayMs = 80) {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3E0))) {
                            Text(
                                text = note,
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                                color = Color(0xFF8A4B00),
                            )
                        }
                    }
                }

                if (state.loading) {
                    ListSkeleton(rows = 3)
                }

                if (!state.loading && state.items.isEmpty() && state.insights.isEmpty()) {
                    MotionReveal(delayMs = 120) {
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                            Text("你还没有关注基金，先去首页加几只看看。", modifier = Modifier.padding(14.dp))
                        }
                    }
                }

                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    if (state.insights.isNotEmpty()) {
                        itemsIndexed(state.insights, key = { _, item -> item.fundCode }) { index, item ->
                            MotionReveal(delayMs = 140 + (index.coerceAtMost(8) * 35)) {
                                WatchlistInsightCard(
                                    item = item,
                                    hasAlert = state.alertFundCodes.contains(item.fundCode),
                                    onClick = { onOpenDetail(item.fundCode) },
                                )
                            }
                        }
                    } else {
                        itemsIndexed(state.items, key = { _, item -> item.fundCode }) { index, item ->
                            MotionReveal(delayMs = 140 + (index.coerceAtMost(8) * 35)) {
                                WatchlistItemCard(
                                    item = item,
                                    hasAlert = state.alertFundCodes.contains(item.fundCode),
                                    onClick = { onOpenDetail(item.fundCode) },
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun OverviewCard(size: Int) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0E3A66)),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("关注数量", color = Color.White.copy(alpha = 0.8f))
                Text("$size", style = MaterialTheme.typography.headlineMedium, color = Color.White)
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.AutoMirrored.Rounded.TrendingUp, contentDescription = "trend", tint = Color(0xFF9ED1FF))
                Text(
                    "持续跟踪",
                    modifier = Modifier.padding(start = 6.dp),
                    color = Color.White.copy(alpha = 0.9f),
                )
            }
        }
    }
}

@Composable
private fun WatchlistInsightCard(
    item: WatchlistInsight,
    hasAlert: Boolean,
    onClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text(item.fundCode, style = MaterialTheme.typography.titleMedium)
                    Text(
                        "信号: ${item.signal} · ${item.actionLabel}",
                        style = MaterialTheme.typography.bodySmall,
                        color = signalColor(item.signal),
                    )
                }
                Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    AlertStatusTag(hasAlert = hasAlert)
                    Text(
                        "风险: ${riskLevelText(item.riskLevel)}${item.riskScore?.let { " · ${it}分" } ?: ""}",
                        color = riskLevelColor(item.riskLevel),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                InsightPill(
                    modifier = Modifier.weight(1f),
                    label = "短期评分",
                    value = scoreOrDash(item.shortScore),
                    color = scoreColor(item.shortScore),
                )
                InsightPill(
                    modifier = Modifier.weight(1f),
                    label = "中期评分",
                    value = scoreOrDash(item.midScore),
                    color = scoreColor(item.midScore),
                )
                InsightPill(
                    modifier = Modifier.weight(1f),
                    label = "行动标签",
                    value = item.actionLabel,
                    color = actionLabelColor(item.actionLabel),
                )
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                InsightPill(
                    modifier = Modifier.weight(1f),
                    label = "短期概率",
                    value = percentOrDash(item.shortUpProbability),
                    color = percentColor(item.shortUpProbability),
                )
                InsightPill(
                    modifier = Modifier.weight(1f),
                    label = "中期概率",
                    value = percentOrDash(item.midUpProbability),
                    color = percentColor(item.midUpProbability),
                )
            }
            if (item.scoreSummary.isNotBlank()) {
                Text(
                    item.scoreSummary,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                "数据新鲜度: ${freshnessText(item.dataFreshness)}",
                style = MaterialTheme.typography.bodySmall,
                color = freshnessColor(item.dataFreshness),
            )
        }
    }
}

@Composable
private fun InsightPill(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    color: Color,
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.12f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.titleSmall, color = color)
        }
    }
}

@Composable
private fun WatchlistItemCard(
    item: WatchlistItem,
    hasAlert: Boolean,
    onClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(item.fundCode, style = MaterialTheme.typography.titleMedium)
                Text("已加入自选池", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
                AlertStatusTag(hasAlert = hasAlert)
            }
            Icon(Icons.Rounded.Star, contentDescription = "watched", tint = Color(0xFFE9B300))
        }
    }
}

@Composable
private fun AlertStatusTag(hasAlert: Boolean) {
    val color = if (hasAlert) Color(0xFF126A57) else Color(0xFF68707D)
    val bg = if (hasAlert) Color(0xFFE6F7F1) else Color(0xFFF1F3F6)
    Row(
        modifier = Modifier
            .background(bg, shape = MaterialTheme.shapes.small)
            .padding(horizontal = 8.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Icon(
            imageVector = if (hasAlert) Icons.Rounded.NotificationsActive else Icons.Rounded.NotificationsNone,
            contentDescription = null,
            tint = color,
        )
        Text(
            text = if (hasAlert) "已设置提醒" else "未设置提醒",
            style = MaterialTheme.typography.bodySmall,
            color = color,
        )
    }
}

private fun percentOrDash(value: Double?): String {
    return value?.let { "${(it * 100).toInt()}%" } ?: "--"
}

private fun scoreOrDash(value: Int?): String {
    return value?.toString() ?: "--"
}

private fun percentColor(value: Double?): Color {
    if (value == null) return Color(0xFF70757F)
    return when {
        value >= 0.6 -> Color(0xFF0B8A43)
        value <= 0.45 -> Color(0xFFC62828)
        else -> Color(0xFF8A6A00)
    }
}

private fun scoreColor(value: Int?): Color {
    if (value == null) return Color(0xFF70757F)
    return when {
        value >= 75 -> Color(0xFF0B8A43)
        value >= 60 -> Color(0xFF0C5B9F)
        value >= 45 -> Color(0xFFB26A00)
        else -> Color(0xFFC62828)
    }
}

private fun actionLabelColor(value: String): Color {
    return when (value) {
        "强关注" -> Color(0xFF0B8A43)
        "关注" -> Color(0xFF126A57)
        "观察" -> Color(0xFFB26A00)
        "回避" -> Color(0xFFC62828)
        else -> Color(0xFF70757F)
    }
}

private fun riskLevelText(value: String): String {
    return when (value.lowercase()) {
        "low" -> "低"
        "medium" -> "中"
        "high" -> "高"
        else -> "未知"
    }
}

private fun riskLevelColor(value: String): Color {
    return when (value.lowercase()) {
        "low" -> Color(0xFF0B8A43)
        "medium" -> Color(0xFFB26A00)
        "high" -> Color(0xFFC62828)
        else -> Color(0xFF70757F)
    }
}

private fun signalColor(value: String): Color {
    return when {
        value.contains("偏多") -> Color(0xFF0B8A43)
        value.contains("偏空") -> Color(0xFFC62828)
        else -> Color(0xFF596072)
    }
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
        else -> Color(0xFF70757F)
    }
}
