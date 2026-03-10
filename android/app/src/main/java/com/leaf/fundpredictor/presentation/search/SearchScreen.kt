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
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.QueryStats
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
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
import com.leaf.fundpredictor.domain.model.Fund
import com.leaf.fundpredictor.presentation.components.ListSkeleton
import com.leaf.fundpredictor.presentation.components.MotionReveal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(
    viewModel: SearchViewModel,
    onOpenDetail: (String) -> Unit,
) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) { viewModel.search() }

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = {
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("基金搜索", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "独立检索页",
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
                MotionReveal(delayMs = 40) {
                    SearchBoxCard(
                        query = state.query,
                        onQueryChange = viewModel::onQueryChange,
                        onSearch = viewModel::search,
                    )
                }

                Text(
                    if (state.query.isBlank()) "当前展示热门基金" else "搜索结果：${state.items.size} 条",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )

                if (state.loading) {
                    ListSkeleton(rows = 5)
                }

                state.error?.let { err ->
                    MotionReveal(delayMs = 60) {
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
                            Text("暂无基金数据，请尝试其他关键词", modifier = Modifier.padding(14.dp))
                        }
                    }
                }

                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    itemsIndexed(state.items, key = { _, fund -> fund.code }) { index, fund ->
                        MotionReveal(delayMs = 80 + (index.coerceAtMost(8) * 25)) {
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
private fun SearchBoxCard(
    query: String,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
) {
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
                    value = query,
                    onValueChange = onQueryChange,
                    label = { Text("基金代码 / 名称") },
                    singleLine = true,
                    leadingIcon = {
                        Icon(Icons.Rounded.QueryStats, contentDescription = "search")
                    },
                )
                Button(onClick = onSearch) {
                    Text("搜索")
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                QuickChip("白酒") { onQueryChange("白酒"); onSearch() }
                QuickChip("消费") { onQueryChange("消费"); onSearch() }
                QuickChip("指数") { onQueryChange("指数"); onSearch() }
            }
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
                    .padding(horizontal = 8.dp, vertical = 10.dp),
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
                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        "代码 ${fund.code}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
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
