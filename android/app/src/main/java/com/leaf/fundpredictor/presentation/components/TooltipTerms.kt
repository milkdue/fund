package com.leaf.fundpredictor.presentation.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.PlainTooltip
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TooltipBox
import androidx.compose.material3.TooltipDefaults
import androidx.compose.material3.rememberTooltipState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LabelWithTooltip(
    label: String,
    tooltip: String,
    modifier: Modifier = Modifier,
    labelColor: Color = MaterialTheme.colorScheme.onSurface,
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Text(label, color = labelColor)
        InfoTooltipIcon(message = tooltip, tint = labelColor.copy(alpha = 0.72f))
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun GlossaryTermsRow(
    terms: List<Pair<String, String>>,
    modifier: Modifier = Modifier,
) {
    FlowRow(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        terms.forEach { (term, explanation) ->
            GlossaryChip(term = term, tooltip = explanation)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GlossaryChip(
    term: String,
    tooltip: String,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        color = Color(0xFFF0F5FF),
        shape = RoundedCornerShape(18.dp),
    ) {
        Row(
            modifier = Modifier.padding(start = 10.dp, top = 4.dp, end = 4.dp, bottom = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text(
                text = term,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
                color = Color(0xFF0C5B9F),
            )
            InfoTooltipIcon(message = tooltip, tint = Color(0xFF0C5B9F))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InfoTooltipIcon(
    message: String,
    tint: Color,
    modifier: Modifier = Modifier,
) {
    val tooltipState = rememberTooltipState(isPersistent = false)
    val scope = rememberCoroutineScope()

    TooltipBox(
        positionProvider = TooltipDefaults.rememberPlainTooltipPositionProvider(),
        tooltip = {
            PlainTooltip {
                Text(
                    text = message,
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp),
                )
            }
        },
        state = tooltipState,
        modifier = modifier,
    ) {
        Box(
            modifier = Modifier
                .size(18.dp)
                .clickable { scope.launch { tooltipState.show() } },
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Rounded.Info,
                contentDescription = message,
                tint = tint,
                modifier = Modifier.size(14.dp),
            )
        }
    }
}
