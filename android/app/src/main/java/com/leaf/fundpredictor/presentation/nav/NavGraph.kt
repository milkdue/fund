package com.leaf.fundpredictor.presentation.nav

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Home
import androidx.compose.material.icons.rounded.NotificationsActive
import androidx.compose.material.icons.rounded.QueryStats
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.leaf.fundpredictor.presentation.alerts.AlertsScreen
import com.leaf.fundpredictor.presentation.alerts.AlertsViewModel
import com.leaf.fundpredictor.presentation.detail.DetailScreen
import com.leaf.fundpredictor.presentation.detail.DetailViewModel
import com.leaf.fundpredictor.presentation.home.HomeScreen
import com.leaf.fundpredictor.presentation.home.HomeViewModel
import com.leaf.fundpredictor.presentation.learn.LearnScreen
import com.leaf.fundpredictor.presentation.risk.RiskScreen
import com.leaf.fundpredictor.presentation.search.SearchScreen
import com.leaf.fundpredictor.presentation.search.SearchViewModel
import com.leaf.fundpredictor.presentation.watchlist.WatchlistScreen
import com.leaf.fundpredictor.presentation.watchlist.WatchlistViewModel

private object Route {
    const val Risk = "risk"
    const val Home = "home"
    const val Search = "search"
    const val Alerts = "alerts"
    const val Watchlist = "watchlist"
    const val Learn = "learn"
    const val Detail = "detail/{code}"
}

@Composable
fun FundNavGraph(
    riskAccepted: Boolean,
    onRiskAccepted: () -> Unit,
) {
    val navController = rememberNavController()
    val startDestination = if (riskAccepted) Route.Home else Route.Risk
    val backStack by navController.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route.orEmpty()
    val showBottomBar = currentRoute == Route.Home || currentRoute == Route.Search || currentRoute == Route.Alerts || currentRoute == Route.Watchlist

    fun navigateTab(route: String) {
        navController.navigate(route) {
            launchSingleTop = true
            restoreState = true
            popUpTo(Route.Home) {
                saveState = true
            }
        }
    }

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(
                    containerColor = Color(0xFFEAF1FF),
                    tonalElevation = 4.dp,
                ) {
                    NavigationBarItem(
                        selected = currentRoute == Route.Home,
                        onClick = {
                            navigateTab(Route.Home)
                        },
                        icon = { Icon(Icons.Rounded.Home, contentDescription = "首页") },
                        label = { Text("首页") },
                        colors = NavigationBarItemDefaults.colors(
                            indicatorColor = Color(0xFFD8E8FF),
                            selectedIconColor = Color(0xFF0C5B9F),
                            selectedTextColor = Color(0xFF0C5B9F),
                        ),
                    )
                    NavigationBarItem(
                        selected = currentRoute == Route.Search,
                        onClick = {
                            navigateTab(Route.Search)
                        },
                        icon = { Icon(Icons.Rounded.QueryStats, contentDescription = "搜索") },
                        label = { Text("搜索") },
                        colors = NavigationBarItemDefaults.colors(
                            indicatorColor = Color(0xFFD8E8FF),
                            selectedIconColor = Color(0xFF0C5B9F),
                            selectedTextColor = Color(0xFF0C5B9F),
                        ),
                    )
                    NavigationBarItem(
                        selected = currentRoute == Route.Watchlist,
                        onClick = {
                            navigateTab(Route.Watchlist)
                        },
                        icon = { Icon(Icons.Rounded.Star, contentDescription = "自选") },
                        label = { Text("自选") },
                        colors = NavigationBarItemDefaults.colors(
                            indicatorColor = Color(0xFFE6F7F1),
                            selectedIconColor = Color(0xFF126A57),
                            selectedTextColor = Color(0xFF126A57),
                        ),
                    )
                    NavigationBarItem(
                        selected = currentRoute == Route.Alerts,
                        onClick = {
                            navigateTab(Route.Alerts)
                        },
                        icon = { Icon(Icons.Rounded.NotificationsActive, contentDescription = "推送") },
                        label = { Text("推送") },
                        colors = NavigationBarItemDefaults.colors(
                            indicatorColor = Color(0xFFE7F2FF),
                            selectedIconColor = Color(0xFF0C5B9F),
                            selectedTextColor = Color(0xFF0C5B9F),
                        ),
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = startDestination,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Route.Risk) {
                RiskScreen(
                    onAgree = {
                        onRiskAccepted()
                        navController.navigate(Route.Home) {
                            popUpTo(Route.Risk) { inclusive = true }
                        }
                    }
                )
            }

            composable(Route.Home) {
                val vm: HomeViewModel = hiltViewModel()
                HomeScreen(
                    viewModel = vm,
                    onOpenSearch = { navigateTab(Route.Search) },
                    onOpenWatchlist = { navigateTab(Route.Watchlist) },
                    onOpenAlerts = { navigateTab(Route.Alerts) },
                    onOpenLearn = { navController.navigate(Route.Learn) },
                    onOpenDetail = { code -> navController.navigate("detail/$code") },
                )
            }

            composable(Route.Search) {
                val vm: SearchViewModel = hiltViewModel()
                SearchScreen(
                    viewModel = vm,
                    onOpenDetail = { code -> navController.navigate("detail/$code") },
                )
            }

            composable(
                route = Route.Detail,
                arguments = listOf(navArgument("code") { type = NavType.StringType })
            ) { backStackEntry ->
                val vm: DetailViewModel = hiltViewModel()
                DetailScreen(
                    code = backStackEntry.arguments?.getString("code").orEmpty(),
                    viewModel = vm,
                    onBack = { navController.popBackStack() },
                )
            }

            composable(Route.Watchlist) {
                val vm: WatchlistViewModel = hiltViewModel()
                WatchlistScreen(
                    viewModel = vm,
                    onBack = { navigateTab(Route.Home) },
                    onOpenDetail = { code -> navController.navigate("detail/$code") },
                )
            }

            composable(Route.Alerts) {
                val vm: AlertsViewModel = hiltViewModel()
                AlertsScreen(viewModel = vm)
            }

            composable(Route.Learn) {
                LearnScreen(
                    onBack = { navController.popBackStack() },
                )
            }
        }
    }
}
