package com.leaf.fundpredictor.presentation.home

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.TrendingUp
import androidx.compose.material.icons.rounded.NotificationsActive
import androidx.compose.material.icons.rounded.QueryStats
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.DataHealth
import com.leaf.fundpredictor.presentation.components.MotionReveal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: HomeViewModel,
    onOpenSearch: () -> Unit,
    onOpenWatchlist: () -> Unit,
    onOpenAlerts: () -> Unit,
) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) { viewModel.load() }

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = {
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("基金趋势仪表盘", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "系统健康 + 今日策略",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent),
            )
        },
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    brush = Brush.verticalGradient(
                        colors = listOf(Color(0xFFE9F3FF), Color(0xFFF6FFF9), Color(0xFFF4F7FD)),
                    ),
                )
                .padding(innerPadding),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                MotionReveal(delayMs = 30) {
                    StrategyBoardCard(health = state.dataHealth)
                }

                state.dataHealth?.let { health ->
                    MotionReveal(delayMs = 55) {
                        SystemHealthCard(health = health)
                    }
                    MotionReveal(delayMs = 80) {
                        SourceStatusCard(health = health)
                    }
                }

                MotionReveal(delayMs = 105) {
                    HomeActionGrid(
                        onOpenSearch = onOpenSearch,
                        onOpenWatchlist = onOpenWatchlist,
                        onOpenAlerts = onOpenAlerts,
                    )
                }

                state.error?.let { err ->
                    MotionReveal(delayMs = 130) {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFEBEE))) {
                            Text(
                                text = err,
                                color = Color(0xFFB71C1C),
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                            )
                        }
                    }
                }

                if (state.loading) {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                        Text("正在刷新首页数据...", modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp))
                    }
                }

                if (state.dataHealth == null && !state.loading) {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                        Text("暂未获取到系统健康数据，请稍后刷新。", modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp))
                    }
                }
            }
        }
    }
}

@Composable
private fun StrategyBoardCard(
    health: DataHealth?,
) {
    val quoteCoverage = health?.quoteCoverage48h ?: 0.0
    val predictionCoverage = health?.predictionCoverage48h ?: 0.0
    val line = when {
        health == null -> "暂未获取到系统健康数据，建议先查看搜索页实时结果。"
        quoteCoverage >= 0.9 && predictionCoverage >= 0.9 -> "数据状态良好，优先关注短期概率 >= 60% 且置信度 >= 55% 的标的。"
        quoteCoverage >= 0.75 && predictionCoverage >= 0.75 -> "覆盖率中等，建议结合 AI 第二意见并降低单次仓位。"
        else -> "数据覆盖偏低，建议减少操作频次，等待下一轮刷新后再决策。"
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    brush = Brush.horizontalGradient(colors = listOf(Color(0xFF0C5B9F), Color(0xFF1B7B63))),
                    shape = MaterialTheme.shapes.large,
                ),
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text("今日策略看板", style = MaterialTheme.typography.titleMedium, color = Color.White)
                Text(
                    line,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.92f),
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.AutoMirrored.Rounded.TrendingUp, contentDescription = "trend", tint = Color.White)
                    Text(
                        "量化 + AI 双引擎辅助",
                        color = Color.White,
                        modifier = Modifier.padding(start = 6.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun SystemHealthCard(health: DataHealth) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("系统数据健康", style = MaterialTheme.typography.titleMedium)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                HealthTile(
                    modifier = Modifier.weight(1f),
                    label = "行情覆盖",
                    value = "${(health.quoteCoverage48h * 100).toInt()}%",
                    color = coverageColor(health.quoteCoverage48h),
                )
                HealthTile(
                    modifier = Modifier.weight(1f),
                    label = "预测覆盖",
                    value = "${(health.predictionCoverage48h * 100).toInt()}%",
                    color = coverageColor(health.predictionCoverage48h),
                )
                HealthTile(
                    modifier = Modifier.weight(1f),
                    label = "基金池",
                    value = "${health.fundPoolSize}",
                    color = Color(0xFF0C5B9F),
                )
            }
            Text(
                "新鲜度：行情 ${freshnessText(health.quoteFreshness)} / 预测 ${freshnessText(health.predictionFreshness)} / 市场 ${freshnessText(health.marketFreshness)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun SourceStatusCard(health: DataHealth) {
    val sourceLine = if (health.sourceStatus.isEmpty()) {
        "数据源状态：暂无"
    } else {
        val joined = health.sourceStatus.entries
            .sortedWith(compareBy<Map.Entry<String, String>> { sourceOrder(it.key) }.thenBy { it.key })
            .joinToString(" · ") { (k, v) -> "${sourceName(k)} ${sourceState(v)}" }
        "数据源状态：$joined"
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Text(
            sourceLine,
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun HealthTile(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    color: Color,
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 7.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text(
                label,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(value, style = MaterialTheme.typography.titleSmall, color = color)
        }
    }
}

@Composable
private fun HomeActionGrid(
    onOpenSearch: () -> Unit,
    onOpenWatchlist: () -> Unit,
    onOpenAlerts: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        FilledTonalButton(
            modifier = Modifier.fillMaxWidth(),
            onClick = onOpenSearch,
        ) {
            Icon(Icons.Rounded.QueryStats, contentDescription = "search")
            Text("去搜索基金", modifier = Modifier.padding(start = 6.dp))
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            OutlinedButton(
                modifier = Modifier.weight(1f),
                onClick = onOpenWatchlist,
            ) {
                Icon(Icons.Rounded.Star, contentDescription = "watchlist")
                Text("我的自选", modifier = Modifier.padding(start = 6.dp))
            }
            OutlinedButton(
                modifier = Modifier.weight(1f),
                onClick = onOpenAlerts,
            ) {
                Icon(Icons.Rounded.NotificationsActive, contentDescription = "alerts")
                Text("推送列表", modifier = Modifier.padding(start = 6.dp))
            }
        }
    }
}

private fun coverageColor(value: Double): Color {
    return when {
        value >= 0.95 -> Color(0xFF0B8A43)
        value >= 0.8 -> Color(0xFFB26A00)
        else -> Color(0xFFC62828)
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

private fun sourceOrder(key: String): Int {
    return when (key.lowercase()) {
        "eastmoney_nav" -> 1
        "eastmoney_news" -> 2
        "eastmoney_market" -> 3
        else -> 99
    }
}

private fun sourceName(key: String): String {
    return when (key.lowercase()) {
        "eastmoney_nav" -> "净值源"
        "eastmoney_news" -> "公告舆情源"
        "eastmoney_market" -> "市场指数源"
        else -> key
    }
}

private fun sourceState(value: String): String {
    return when (value.lowercase()) {
        "ok" -> "正常"
        "degraded" -> "降级"
        "stale" -> "过期"
        else -> "未知"
    }
}
