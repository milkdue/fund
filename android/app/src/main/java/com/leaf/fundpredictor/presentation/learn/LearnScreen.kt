package com.leaf.fundpredictor.presentation.learn

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.AutoGraph
import androidx.compose.material.icons.rounded.ChecklistRtl
import androidx.compose.material.icons.rounded.QueryStats
import androidx.compose.material.icons.rounded.Schedule
import androidx.compose.material.icons.rounded.School
import androidx.compose.material.icons.rounded.WarningAmber
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.leaf.fundpredictor.presentation.components.GlossaryTermsRow
import com.leaf.fundpredictor.presentation.components.LabelWithTooltip
import com.leaf.fundpredictor.presentation.components.MotionReveal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LearnScreen(onBack: () -> Unit) {
    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = {
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("新手判断理论")
                        Text(
                            "先判断方向，再判断空间",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
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
                        colors = listOf(Color(0xFFF0F6FF), Color(0xFFF7FFF9), Color(0xFFFFFCF5)),
                    ),
                )
                .padding(innerPadding),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                MotionReveal(delayMs = 20) {
                    HeroCard()
                }

                MotionReveal(delayMs = 45) {
                    SectionCard(
                        title = "1. 先理解股价为什么会动",
                        subtitle = "股价本质由价值、预期、交易三层共同驱动。",
                        accent = Color(0xFF0C5B9F),
                        icon = Icons.Rounded.School,
                    ) {
                        InsightRow(
                            title = "价值",
                            body = "公司未来能赚多少钱，长期决定价格中枢。",
                        )
                        InsightRow(
                            title = "预期",
                            body = "市场原来怎么想，现在有没有上修或下修。",
                        )
                        InsightRow(
                            title = "交易",
                            body = "短期资金、消息、情绪决定价格偏离到哪里。",
                        )
                    }
                }

                MotionReveal(delayMs = 70) {
                    SectionCard(
                        title = "2. 判断大概率涨跌，看这 6 个维度",
                        subtitle = "方向不是看单一指标，而是六个维度是否同向共振。",
                        accent = Color(0xFF126A57),
                        icon = Icons.Rounded.AutoGraph,
                    ) {
                        InsightRow(
                            title = "基本面",
                            body = "收入、利润、毛利率、现金流是否改善，尤其看业绩预期有没有上修。",
                        )
                        InsightRow(
                            title = "估值",
                            body = "和历史估值、同行估值、增长速度相比，当前是否过贵或被低估。",
                        )
                        InsightRow(
                            title = "行业与大盘",
                            body = "板块是不是顺风期，政策、利率、流动性是否支持这个方向。",
                        )
                        InsightRow(
                            title = "资金与筹码",
                            body = "是否放量上涨、是否持续流入、上方套牢盘和减持解禁是否压制。",
                        )
                        InsightRow(
                            title = "技术面",
                            body = "趋势是否向上，回踩支撑是否有效，MACD/RSI/均线是否配合。",
                        )
                        GlossaryTermsRow(
                            terms = listOf(
                                "MACD" to "指数平滑异同平均线，用来看趋势是否增强或转弱。",
                                "RSI" to "相对强弱指标，用来看短期是否过热或过冷。",
                            ),
                        )
                        InsightRow(
                            title = "催化剂",
                            body = "财报、政策、订单、回购、并购等事件，常常是趋势加速器。",
                        )
                    }
                }

                MotionReveal(delayMs = 95) {
                    SectionCard(
                        title = "3. 判断涨多少跌多少，看这 3 个方法",
                        subtitle = "不要猜精确点位，应该先做区间和场景。",
                        accent = Color(0xFF935E0E),
                        icon = Icons.Rounded.QueryStats,
                    ) {
                        InsightRow(
                            title = "估值法",
                            body = "目标价 = 未来每股收益（EPS） × 合理市盈率（PE）。适合判断中期空间。",
                        )
                        InsightRow(
                            title = "情景分析",
                            body = "分乐观、基准、悲观三种场景，先看上行空间，再看下行风险。",
                        )
                        InsightRow(
                            title = "波动率法",
                            body = "短线更适合看 ATR、20 日波动率、财报日前后平均振幅。",
                        )
                        GlossaryTermsRow(
                            terms = listOf(
                                "EPS" to "每股收益，代表公司每一股能赚多少钱。",
                                "PE" to "市盈率，代表市场愿意给公司多少倍利润估值。",
                                "ATR" to "平均真实波幅，用来看股票通常一天波动有多大。",
                            ),
                        )
                    }
                }

                MotionReveal(delayMs = 120) {
                    SectionCard(
                        title = "4. 不同周期，看不同东西",
                        subtitle = "短期、中期、长期的判断逻辑并不一样。",
                        accent = Color(0xFF7A4CB6),
                        icon = Icons.Rounded.Schedule,
                    ) {
                        HorizonCard(
                            title = "短期 1-5 天",
                            body = "更看消息、情绪、资金、技术面，尤其看量价和事件驱动。",
                        )
                        HorizonCard(
                            title = "中期 1-3 月",
                            body = "更看业绩预期变化、行业景气、估值修复和机构资金流向。",
                        )
                        HorizonCard(
                            title = "长期 1 年以上",
                            body = "最终回到商业模式、盈利质量、现金流和护城河。",
                        )
                    }
                }

                MotionReveal(delayMs = 145) {
                    SectionCard(
                        title = "5. 小白实际操作时，就按这张清单走",
                        subtitle = "这比盯着涨跌榜更有用。",
                        accent = Color(0xFF0C5B9F),
                        icon = Icons.Rounded.ChecklistRtl,
                    ) {
                        ChecklistItem(number = 1, text = "先看大盘和板块是不是顺风。")
                        ChecklistItem(number = 2, text = "再看公司或基金对应资产的基本面有没有变好。")
                        ChecklistItem(number = 3, text = "确认估值没有离谱透支。")
                        ChecklistItem(number = 4, text = "看趋势、成交量、筹码结构是否健康。")
                        ChecklistItem(number = 5, text = "最后检查未来 1-4 周有没有关键催化剂或风险事件。")
                    }
                }

                MotionReveal(delayMs = 170) {
                    SectionCard(
                        title = "6. 你在 App 里应该怎么读结果",
                        subtitle = "量化预测和 AI 第二意见，适合按这个顺序看。",
                        accent = Color(0xFF126A57),
                        icon = Icons.Rounded.AutoGraph,
                    ) {
                        InsightRow(
                            title = "先看量化预测",
                            body = "重点看上涨概率、置信度、预期涨跌幅、波动率和风险等级。",
                        )
                        InsightRow(
                            title = "再看 AI 第二意见",
                            body = "它负责把量化、行情、新闻和市场背景翻译成人话，不负责替你做决定。",
                        )
                        GlossaryTermsRow(
                            terms = listOf(
                                "AI" to "人工智能。这里的作用是做第二意见和文字解释，不是替你自动下单。",
                            ),
                        )
                        InsightRow(
                            title = "最后做盈亏比判断",
                            body = "不是问会不会涨，而是问上涨空间是否足够覆盖下跌风险。",
                        )
                    }
                }

                MotionReveal(delayMs = 195) {
                    SectionCard(
                        title = "7. 风险提醒",
                        subtitle = "下面这些情况出现时，应该主动降低信号权重。",
                        accent = Color(0xFFC62828),
                        icon = Icons.Rounded.WarningAmber,
                    ) {
                        InsightRow(
                            title = "只凭单一消息",
                            body = "单条消息常常只会带来短线波动，不能替代完整判断。",
                        )
                        InsightRow(
                            title = "高估值叠加高情绪",
                            body = "即使方向没错，也容易在高位回撤里承受大波动。",
                        )
                        InsightRow(
                            title = "数据过期或覆盖不足",
                            body = "当系统健康较差时，应减少交易频率，优先观察而不是下结论。",
                        )
                        Text(
                            "本页面仅用于帮助理解判断逻辑，不构成投资建议。",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF8B1E1E),
                            modifier = Modifier.padding(top = 4.dp),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HeroCard() {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    brush = Brush.linearGradient(
                        colors = listOf(Color(0xFF0D5C9F), Color(0xFF1E7F63), Color(0xFFB77A1A)),
                    ),
                    shape = RoundedCornerShape(28.dp),
                ),
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 18.dp, vertical = 18.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    "涨跌判断不是猜测，\n而是在做概率和空间评估。",
                    style = MaterialTheme.typography.headlineSmall,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    "先判断方向，再判断空间，最后判断盈亏比。",
                    style = MaterialTheme.typography.bodyLarge,
                    color = Color.White.copy(alpha = 0.92f),
                )
                LabelWithTooltip(
                    label = "为什么不直接猜点位？",
                    tooltip = "因为投资判断更应该先看上涨概率、下跌风险和盈亏比，而不是迷信一个精确价格。",
                    labelColor = Color.White,
                )
            }
        }
    }
}

@Composable
private fun SectionCard(
    title: String,
    subtitle: String,
    accent: Color,
    icon: ImageVector,
    content: @Composable () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Surface(
                    color = accent.copy(alpha = 0.14f),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = accent,
                        modifier = Modifier.padding(10.dp),
                    )
                }
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(title, style = MaterialTheme.typography.titleMedium)
                    Text(
                        subtitle,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            content()
        }
    }
}

@Composable
private fun InsightRow(
    title: String,
    body: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            title,
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            body,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun HorizonCard(
    title: String,
    body: String,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF6F8FB)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleSmall)
            Text(
                body,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun ChecklistItem(
    number: Int,
    text: String,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Surface(
            color = Color(0xFFE2EEFF),
            shape = RoundedCornerShape(14.dp),
            modifier = Modifier.size(32.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(number.toString(), color = Color(0xFF0C5B9F), fontWeight = FontWeight.Bold)
            }
        }
        Text(
            text,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.weight(1f),
        )
    }
}
