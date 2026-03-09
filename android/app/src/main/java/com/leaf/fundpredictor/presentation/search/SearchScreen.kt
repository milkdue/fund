package com.leaf.fundpredictor.presentation.search

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.presentation.components.ListSkeleton

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
        topBar = {
            TopAppBar(
                title = { Text(if (state.query.isBlank()) "热门基金" else "搜索结果", style = MaterialTheme.typography.titleLarge) }
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedTextField(
                    modifier = Modifier.weight(1f),
                    value = state.query,
                    onValueChange = viewModel::onQueryChange,
                    label = { Text("基金代码 / 名称") },
                    singleLine = true,
                )
                Button(onClick = viewModel::search) { Text("搜索") }
            }

            Button(onClick = onOpenWatchlist, modifier = Modifier.fillMaxWidth()) {
                Text("进入我的自选")
            }

            if (state.loading) {
                ListSkeleton(rows = 4)
            }

            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

            if (!state.loading && state.items.isEmpty()) {
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                    Text("暂无基金数据，请尝试其他关键词", modifier = Modifier.padding(14.dp), style = MaterialTheme.typography.bodyMedium)
                }
            }

            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(state.items) { fund ->
                    Card(
                        modifier = Modifier.fillMaxWidth().clickable { onOpenDetail(fund.code) },
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    ) {
                        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(fund.name, style = MaterialTheme.typography.titleMedium)
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text("代码: ${fund.code}", style = MaterialTheme.typography.bodyMedium)
                                AssistChip(onClick = {}, label = { Text(fund.category) })
                            }
                        }
                    }
                }
            }
        }
    }
}
