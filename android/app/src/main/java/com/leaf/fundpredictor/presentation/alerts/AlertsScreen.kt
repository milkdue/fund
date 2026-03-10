package com.leaf.fundpredictor.presentation.alerts

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
import androidx.compose.material.icons.rounded.NotificationsActive
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
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
import com.leaf.fundpredictor.presentation.components.ListSkeleton
import com.leaf.fundpredictor.presentation.components.MotionReveal
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AlertsScreen(
    viewModel: AlertsViewModel,
) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) { viewModel.load() }

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = {
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("推送列表", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "最近触发提醒",
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
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                MotionReveal(delayMs = 30) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFEFF6FF)),
                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 14.dp, vertical = 12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    Icons.Rounded.NotificationsActive,
                                    contentDescription = "alerts",
                                    tint = Color(0xFF0C5B9F),
                                )
                                Text(
                                    "已记录 ${state.items.size} 条提醒",
                                    style = MaterialTheme.typography.titleMedium,
                                    modifier = Modifier.padding(start = 6.dp),
                                )
                            }
                        }
                    }
                }

                if (state.loading) {
                    ListSkeleton(rows = 5)
                }

                state.error?.let { err ->
                    MotionReveal(delayMs = 50) {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFEBEE))) {
                            Text(
                                text = err,
                                color = Color(0xFFB71C1C),
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                            )
                        }
                    }
                }

                if (!state.loading && state.items.isEmpty()) {
                    MotionReveal(delayMs = 70) {
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                            Text("暂无推送记录，先在详情页设置阈值提醒。", modifier = Modifier.padding(14.dp))
                        }
                    }
                }

                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    itemsIndexed(state.items, key = { _, item -> item.id }) { index, item ->
                        MotionReveal(delayMs = 80 + (index.coerceAtMost(8) * 25)) {
                            AlertRow(item = item)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AlertRow(item: AlertEvent) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                "${item.fundCode} · ${horizonText(item.horizon)} · ${formatEventTime(item.createdAt)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(item.message, style = MaterialTheme.typography.bodyMedium)
        }
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
