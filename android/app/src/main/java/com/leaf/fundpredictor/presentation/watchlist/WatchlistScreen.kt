package com.leaf.fundpredictor.presentation.watchlist

import androidx.compose.foundation.background
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
import com.leaf.fundpredictor.domain.model.AlertEvent
import com.leaf.fundpredictor.domain.model.WatchlistInsight
import com.leaf.fundpredictor.domain.model.WatchlistItem
import com.leaf.fundpredictor.presentation.components.ListSkeleton
import com.leaf.fundpredictor.presentation.components.MotionReveal
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WatchlistScreen(viewModel: WatchlistViewModel, onBack: () -> Unit) {
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
                    if (state.alertEvents.isNotEmpty()) {
                        item {
                            MotionReveal(delayMs = 125) {
                                AlertEventsCard(items = state.alertEvents.take(6))
                            }
                        }
                    }
                    if (state.insights.isNotEmpty()) {
                        itemsIndexed(state.insights, key = { _, item -> item.fundCode }) { index, item ->
                            MotionReveal(delayMs = 140 + (index.coerceAtMost(8) * 35)) {
                                WatchlistInsightCard(item = item)
                            }
                        }
                    } else {
                        itemsIndexed(state.items, key = { _, item -> item.fundCode }) { index, item ->
                            MotionReveal(delayMs = 140 + (index.coerceAtMost(8) * 35)) {
                                WatchlistItemCard(item = item)
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
private fun AlertEventsCard(items: List<AlertEvent>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFEFF6FF)),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(7.dp),
        ) {
            Text("推送列表（最近触发）", style = MaterialTheme.typography.titleMedium)
            items.forEach { item ->
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(
                        "${item.fundCode} · ${horizonText(item.horizon)} · ${formatEventTime(item.createdAt)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Text(item.message, style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }
}

@Composable
private fun WatchlistInsightCard(item: WatchlistInsight) {
    Card(
        modifier = Modifier.fillMaxWidth(),
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
                    Text("信号: ${item.signal}", style = MaterialTheme.typography.bodySmall, color = signalColor(item.signal))
                }
                Text(
                    "风险: ${riskLevelText(item.riskLevel)}",
                    color = riskLevelColor(item.riskLevel),
                    style = MaterialTheme.typography.bodySmall,
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
private fun WatchlistItemCard(item: WatchlistItem) {
    Card(
        modifier = Modifier.fillMaxWidth(),
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
            }
            Icon(Icons.Rounded.Star, contentDescription = "watched", tint = Color(0xFFE9B300))
        }
    }
}

private fun percentOrDash(value: Double?): String {
    return value?.let { "${(it * 100).toInt()}%" } ?: "--"
}

private fun percentColor(value: Double?): Color {
    if (value == null) return Color(0xFF70757F)
    return when {
        value >= 0.6 -> Color(0xFF0B8A43)
        value <= 0.45 -> Color(0xFFC62828)
        else -> Color(0xFF8A6A00)
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

private fun horizonText(value: String): String {
    return when (value.lowercase()) {
        "short" -> "短期"
        "mid" -> "中期"
        else -> value
    }
}

private fun formatEventTime(raw: String): String {
    val fmt = DateTimeFormatter.ofPattern("MM-dd HH:mm")
    return runCatching {
        OffsetDateTime.parse(raw).format(fmt)
    }.recoverCatching {
        LocalDateTime.parse(raw).format(fmt)
    }.getOrElse { raw }
}
