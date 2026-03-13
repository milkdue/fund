package com.leaf.fundpredictor.presentation.watchlist

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.TrendingUp
import androidx.compose.material.icons.rounded.NotificationsActive
import androidx.compose.material.icons.rounded.NotificationsNone
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.domain.model.ScoreCard
import com.leaf.fundpredictor.domain.model.WatchlistInsight
import com.leaf.fundpredictor.domain.model.WatchlistItem
import com.leaf.fundpredictor.presentation.components.LabelWithTooltip
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
    var scoreSheet by remember { mutableStateOf<WatchlistScoreSheetState?>(null) }
    var filter by remember { mutableStateOf(WatchlistFilter.All) }
    val filteredInsights = remember(state.insights, state.alertFundCodes, filter) {
        state.insights.filter { insight ->
            when (filter) {
                WatchlistFilter.All -> true
                WatchlistFilter.Focus -> insight.actionLabel in setOf("强关注", "关注")
                WatchlistFilter.AlertFocus -> state.alertFundCodes.contains(insight.fundCode) && insight.actionLabel in setOf("强关注", "关注")
                WatchlistFilter.MissingAlert -> !state.alertFundCodes.contains(insight.fundCode)
                WatchlistFilter.Stale -> insight.dataFreshness.lowercase() != "fresh"
            }
        }
    }
    val filteredItems = remember(state.items, state.alertFundCodes, filter) {
        state.items.filter { item ->
            when (filter) {
                WatchlistFilter.All -> true
                WatchlistFilter.AlertFocus -> state.alertFundCodes.contains(item.fundCode)
                WatchlistFilter.MissingAlert -> !state.alertFundCodes.contains(item.fundCode)
                WatchlistFilter.Focus -> true
                WatchlistFilter.Stale -> true
            }
        }
    }
    val highlights = remember(state.insights, state.items, state.alertFundCodes) {
        deriveWatchlistHighlights(
            insights = state.insights,
            items = state.items,
            alertFundCodes = state.alertFundCodes,
        )
    }

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
                actions = {
                    IconButton(
                        enabled = !state.loading && !state.refreshing,
                        onClick = { viewModel.refresh() },
                    ) {
                        if (state.refreshing) {
                            CircularProgressIndicator(
                                modifier = Modifier.padding(4.dp),
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
                if (state.refreshing) {
                    MotionReveal(delayMs = 12) {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F3FF))) {
                            Text(
                                "正在刷新自选洞察，当前内容已保留。",
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                                color = Color(0xFF0C5B9F),
                            )
                        }
                    }
                }

                state.lastRefreshedAt?.let { refreshedAt ->
                    MotionReveal(delayMs = 18) {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFF8FBFF))) {
                            Text(
                                "上次刷新：$refreshedAt",
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }

                MotionReveal(delayMs = 40) {
                    OverviewCard(highlights = highlights)
                }

                MotionReveal(delayMs = 60) {
                    FilterBar(
                        current = filter,
                        displayedCount = if (state.insights.isNotEmpty()) filteredInsights.size else filteredItems.size,
                        totalCount = maxOf(state.insights.size, state.items.size),
                        onSelect = { filter = it },
                    )
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

                if (!state.loading && state.insights.isNotEmpty() && filteredInsights.isEmpty()) {
                    MotionReveal(delayMs = 126) {
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                            Text(
                                "当前筛选下没有结果，换一个筛选条件试试。",
                                modifier = Modifier.padding(14.dp),
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }

                if (!state.loading && state.insights.isEmpty() && state.items.isNotEmpty() && filteredItems.isEmpty()) {
                    MotionReveal(delayMs = 126) {
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                            Text(
                                "当前筛选下没有自选项可展示。",
                                modifier = Modifier.padding(14.dp),
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }

                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    if (state.insights.isNotEmpty()) {
                        itemsIndexed(filteredInsights, key = { _, item -> item.fundCode }) { index, item ->
                            MotionReveal(delayMs = 140 + (index.coerceAtMost(8) * 35)) {
                                WatchlistInsightCard(
                                    rank = index + 1,
                                    item = item,
                                    hasAlert = state.alertFundCodes.contains(item.fundCode),
                                    onOpenShortScore = {
                                        item.shortScorecard?.let { card ->
                                            scoreSheet = WatchlistScoreSheetState(
                                                title = "${item.fundCode} · 短期评分依据",
                                                scorecard = card,
                                            )
                                        }
                                    },
                                    onOpenMidScore = {
                                        item.midScorecard?.let { card ->
                                            scoreSheet = WatchlistScoreSheetState(
                                                title = "${item.fundCode} · 中期评分依据",
                                                scorecard = card,
                                            )
                                        }
                                    },
                                    onOpenAction = {
                                        val card = item.shortScorecard ?: item.midScorecard ?: return@WatchlistInsightCard
                                        scoreSheet = WatchlistScoreSheetState(
                                            title = "${item.fundCode} · 评分依据",
                                            scorecard = card,
                                        )
                                    },
                                    onClick = { onOpenDetail(item.fundCode) },
                                )
                            }
                        }
                    } else {
                        itemsIndexed(filteredItems, key = { _, item -> item.fundCode }) { index, item ->
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

            scoreSheet?.let { sheet ->
                WatchlistScoreExplanationSheet(
                    title = sheet.title,
                    scorecard = sheet.scorecard,
                    onDismiss = { scoreSheet = null },
                )
            }
        }
    }
}

private data class WatchlistScoreSheetState(
    val title: String,
    val scorecard: ScoreCard,
)

private enum class WatchlistFilter(val label: String) {
    All("全部"),
    Focus("优先看"),
    AlertFocus("已提醒重点"),
    MissingAlert("未设提醒"),
    Stale("数据滞后"),
}

private data class WatchlistHighlights(
    val totalCount: Int,
    val focusCount: Int,
    val alertedFocusCount: Int,
    val missingAlertCount: Int,
    val staleCount: Int,
)

@Composable
private fun OverviewCard(highlights: WatchlistHighlights) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0E3A66)),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("关注数量", color = Color.White.copy(alpha = 0.8f))
                    Text("${highlights.totalCount}", style = MaterialTheme.typography.headlineMedium, color = Color.White)
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
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OverviewStatTile(
                    modifier = Modifier.weight(1f),
                    label = "优先看",
                    value = "${highlights.focusCount}",
                    valueColor = Color(0xFF9EF1C6),
                )
                OverviewStatTile(
                    modifier = Modifier.weight(1f),
                    label = "已提醒重点",
                    value = "${highlights.alertedFocusCount}",
                    valueColor = Color(0xFFA9D5FF),
                )
                OverviewStatTile(
                    modifier = Modifier.weight(1f),
                    label = "未设提醒",
                    value = "${highlights.missingAlertCount}",
                    valueColor = Color(0xFFFFD08A),
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OverviewStatTile(
                    modifier = Modifier.weight(1f),
                    label = "数据滞后",
                    value = "${highlights.staleCount}",
                    valueColor = Color(0xFFFFA9A1),
                )
                Box(modifier = Modifier.weight(1f).height(1.dp))
                Box(modifier = Modifier.weight(1f).height(1.dp))
            }
        }
    }
}

@Composable
private fun OverviewStatTile(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    valueColor: Color,
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = Color.White.copy(alpha = 0.08f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(3.dp),
        ) {
            Text(label, style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.78f))
            Text(value, style = MaterialTheme.typography.titleMedium, color = valueColor)
        }
    }
}

@Composable
private fun FilterBar(
    current: WatchlistFilter,
    displayedCount: Int,
    totalCount: Int,
    onSelect: (WatchlistFilter) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            WatchlistFilter.entries.forEach { item ->
                FilterChip(
                    selected = current == item,
                    onClick = { onSelect(item) },
                    label = { Text(item.label) },
                )
            }
        }
        Text(
            "当前展示 $displayedCount / $totalCount",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun WatchlistInsightCard(
    rank: Int,
    item: WatchlistInsight,
    hasAlert: Boolean,
    onOpenShortScore: () -> Unit,
    onOpenMidScore: () -> Unit,
    onOpenAction: () -> Unit,
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
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(item.fundCode, style = MaterialTheme.typography.titleMedium)
                        RankTag(rank = rank, actionLabel = item.actionLabel)
                    }
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
                    tooltip = "短期评分综合了方向、空间、市场、舆情、风险和可信度。${item.scoreSummary}",
                    onClick = if (item.shortScorecard != null) onOpenShortScore else null,
                )
                InsightPill(
                    modifier = Modifier.weight(1f),
                    label = "中期评分",
                    value = scoreOrDash(item.midScore),
                    color = scoreColor(item.midScore),
                    tooltip = "中期评分更看趋势延续、市场环境和风险控制。${item.scoreSummary}",
                    onClick = if (item.midScorecard != null) onOpenMidScore else null,
                )
                InsightPill(
                    modifier = Modifier.weight(1f),
                    label = "行动标签",
                    value = item.actionLabel,
                    color = actionLabelColor(item.actionLabel),
                    tooltip = actionLabelTooltip(item.actionLabel),
                    onClick = if (item.shortScorecard != null || item.midScorecard != null) onOpenAction else null,
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
private fun RankTag(rank: Int, actionLabel: String) {
    val color = actionLabelColor(actionLabel)
    Row(
        modifier = Modifier
            .background(color.copy(alpha = 0.12f), shape = MaterialTheme.shapes.small)
            .padding(horizontal = 8.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = "优先级 #$rank",
            style = MaterialTheme.typography.labelMedium,
            color = color,
        )
    }
}

@Composable
private fun InsightPill(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    color: Color,
    tooltip: String? = null,
    onClick: (() -> Unit)? = null,
) {
    Card(
        modifier = if (onClick != null) modifier.clickable(onClick = onClick) else modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.12f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
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
private fun WatchlistScoreExplanationSheet(
    title: String,
    scorecard: ScoreCard,
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
                "${scorecard.actionLabel} · 综合 ${scorecard.totalScore} · 风险 ${scorecard.riskScore}",
                style = MaterialTheme.typography.titleSmall,
                color = actionLabelColor(scorecard.actionLabel),
            )
            Text(
                scorecard.summary,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            scorecard.components.forEach { component ->
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
                                color = scoreColor(component.score),
                            )
                        }
                        Text(
                            component.summary,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        if (component.detailLines.isNotEmpty()) {
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
                    }
                }
            }
            Box(modifier = Modifier.padding(bottom = 18.dp))
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

private fun actionLabelTooltip(value: String): String {
    return when (value) {
        "强关注" -> "强关注表示综合评分处于高位，方向和风险控制都相对更优。"
        "关注" -> "关注表示信号整体较好，但还没有强到最高优先级。"
        "观察" -> "观察表示当前仍有不确定性，更适合持续跟踪。"
        "回避" -> "回避表示当前信号和风险收益比不理想。"
        else -> "行动标签用于快速总结当前评分结论。"
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

private fun deriveWatchlistHighlights(
    insights: List<WatchlistInsight>,
    items: List<WatchlistItem>,
    alertFundCodes: Set<String>,
): WatchlistHighlights {
    if (insights.isNotEmpty()) {
        return WatchlistHighlights(
            totalCount = insights.size,
            focusCount = insights.count { it.actionLabel in setOf("强关注", "关注") },
            alertedFocusCount = insights.count { it.actionLabel in setOf("强关注", "关注") && alertFundCodes.contains(it.fundCode) },
            missingAlertCount = insights.count { !alertFundCodes.contains(it.fundCode) },
            staleCount = insights.count { it.dataFreshness.lowercase() != "fresh" },
        )
    }
    return WatchlistHighlights(
        totalCount = items.size,
        focusCount = 0,
        alertedFocusCount = items.count { alertFundCodes.contains(it.fundCode) },
        missingAlertCount = items.count { !alertFundCodes.contains(it.fundCode) },
        staleCount = 0,
    )
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
