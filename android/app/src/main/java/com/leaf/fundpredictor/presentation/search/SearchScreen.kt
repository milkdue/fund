package com.leaf.fundpredictor.presentation.search

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.TrendingUp
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.QueryStats
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.DataHealth
import com.leaf.fundpredictor.domain.model.Fund
import com.leaf.fundpredictor.presentation.components.ListSkeleton
import com.leaf.fundpredictor.presentation.components.MotionReveal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(
    viewModel: SearchViewModel,
    onOpenDetail: (String) -> Unit,
    onOpenWatchlist: () -> Unit,
) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) { viewModel.search() }

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = {
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("基金趋势仪表盘", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "量化模型 + AI第二意见",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
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
                        colors = listOf(Color(0xFFE9F3FF), Color(0xFFF6FFF9), Color(0xFFF4F7FD))
                    )
                )
                .padding(innerPadding)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                MotionReveal(delayMs = 40) {
                    HeroCard(itemCount = state.items.size, query = state.query)
                }

                state.dataHealth?.let { health ->
                    MotionReveal(delayMs = 70) {
                        SystemHealthCard(health = health)
                    }
                }

                MotionReveal(delayMs = 110) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(14.dp),
                            verticalArrangement = Arrangement.spacedBy(10.dp),
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                OutlinedTextField(
                                    modifier = Modifier.weight(1f),
                                    value = state.query,
                                    onValueChange = viewModel::onQueryChange,
                                    label = { Text("基金代码 / 名称") },
                                    singleLine = true,
                                    leadingIcon = {
                                        Icon(Icons.Rounded.QueryStats, contentDescription = "search")
                                    },
                                )
                                Button(onClick = viewModel::search) {
                                    Text("搜索")
                                }
                            }

                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                QuickChip("白酒") {
                                    viewModel.onQueryChange("白酒")
                                    viewModel.search()
                                }
                                QuickChip("消费") {
                                    viewModel.onQueryChange("消费")
                                    viewModel.search()
                                }
                                QuickChip("指数") {
                                    viewModel.onQueryChange("指数")
                                    viewModel.search()
                                }
                            }

                            FilledTonalButton(onClick = onOpenWatchlist, modifier = Modifier.fillMaxWidth()) {
                                Icon(Icons.Rounded.Star, contentDescription = "watchlist")
                                Text("进入我的自选", modifier = Modifier.padding(start = 6.dp))
                            }
                        }
                    }
                }

                if (state.loading) {
                    ListSkeleton(rows = 4)
                }

                state.error?.let {
                    MotionReveal(delayMs = 130) {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFEBEE))) {
                            Text(
                                text = it,
                                color = Color(0xFFB71C1C),
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                            )
                        }
                    }
                }

                if (!state.loading && state.items.isEmpty()) {
                    MotionReveal(delayMs = 150) {
                        EmptyFundsCard()
                    }
                }

                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    itemsIndexed(state.items, key = { _, fund -> fund.code }) { index, fund ->
                        MotionReveal(delayMs = 170 + (index.coerceAtMost(8) * 35)) {
                            FundListItem(
                                fund = fund,
                                onClick = { onOpenDetail(fund.code) },
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun HeroCard(itemCount: Int, query: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
        modifier = Modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.large)
            .background(
                brush = Brush.horizontalGradient(
                    colors = listOf(Color(0xFF0C5B9F), Color(0xFF1B7B63))
                )
            ),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text("今日策略看板", style = MaterialTheme.typography.titleMedium, color = Color.White)
            Text(
                if (query.isBlank()) "当前展示热门基金候选，点击卡片进入详情。"
                else "检索关键词：$query",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.92f),
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.AutoMirrored.Rounded.TrendingUp, contentDescription = "trend", tint = Color.White)
                    Text(
                        "共 $itemCount 条基金结果",
                        color = Color.White,
                        modifier = Modifier.padding(start = 6.dp),
                    )
                }
                Text("MVP 内测版", color = Color.White.copy(alpha = 0.82f))
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
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
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
            Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.titleSmall, color = color)
        }
    }
}

@Composable
private fun QuickChip(text: String, onClick: () -> Unit) {
    AssistChip(
        onClick = onClick,
        label = { Text(text) },
        colors = AssistChipDefaults.assistChipColors(containerColor = Color(0xFFE7F1FF)),
    )
}

@Composable
private fun EmptyFundsCard() {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Text(
            "暂无基金数据，请尝试其他关键词",
            modifier = Modifier.padding(14.dp),
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun FundListItem(
    fund: Fund,
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
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(10.dp))
                    .background(Color(0xFFE6F3FF))
                    .padding(horizontal = 8.dp, vertical = 10.dp)
            ) {
                Text(fund.code.takeLast(3), color = Color(0xFF0C5B9F))
            }
            Column(
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = 10.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text(fund.name, style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("代码 ${fund.code}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    AssistChip(onClick = {}, label = { Text(fund.category) })
                }
            }
            Icon(
                imageVector = Icons.Rounded.ChevronRight,
                contentDescription = "open",
                tint = MaterialTheme.colorScheme.primary,
            )
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
