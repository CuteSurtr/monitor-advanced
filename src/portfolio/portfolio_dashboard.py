"""
Portfolio Dashboard Module

Provides a Dash-based web dashboard for portfolio management with
interactive visualizations for positions, performance, rebalancing,
and tax optimization.
"""

import dash
from dash import dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime, timedelta
import logging

from src.portfolio.portfolio_manager import (
    PortfolioManager,
    Transaction,
    Position,
    PerformanceMetrics,
    RebalancingSuggestion,
    TaxOptimization,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioDashboard:
    """
    Portfolio management dashboard with interactive visualizations.

    Provides comprehensive portfolio tracking, performance analysis,
    rebalancing suggestions, and tax optimization visualization.
    """

    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio_manager = portfolio_manager
        self.logger = logger

        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )

        # Setup layout
        self.app.layout = self._create_layout()

        # Setup callbacks
        self._setup_callbacks()

    def _create_layout(self) -> html.Div:
        """Create the dashboard layout."""
        return html.Div(
            [
                # Header
                dbc.Navbar(
                    dbc.Container(
                        [
                            dbc.NavbarBrand(
                                "Portfolio Management Dashboard", className="ms-2"
                            ),
                            dbc.Nav(
                                [
                                    dbc.NavItem(
                                        dbc.NavLink("Overview", href="#overview")
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink("Positions", href="#positions")
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink("Performance", href="#performance")
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink("Rebalancing", href="#rebalancing")
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink("Tax Optimization", href="#tax")
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink(
                                            "Transactions", href="#transactions"
                                        )
                                    ),
                                ]
                            ),
                        ]
                    ),
                    color="primary",
                    dark=True,
                    className="mb-4",
                ),
                # Main content
                dbc.Container(
                    [
                        # Overview Section
                        html.Div(
                            id="overview-section",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "Portfolio Overview"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                dbc.Row(
                                                                    [
                                                                        dbc.Col(
                                                                            [
                                                                                html.H4(
                                                                                    id="total-value",
                                                                                    children="Total Value: $0",
                                                                                ),
                                                                                html.P(
                                                                                    id="total-pnl",
                                                                                    children="Total P&L: $0 (0%)",
                                                                                ),
                                                                            ],
                                                                            width=6,
                                                                        ),
                                                                        dbc.Col(
                                                                            [
                                                                                html.H4(
                                                                                    id="total-positions",
                                                                                    children="Positions: 0",
                                                                                ),
                                                                                html.P(
                                                                                    id="total-return",
                                                                                    children="Total Return: 0%",
                                                                                ),
                                                                            ],
                                                                            width=6,
                                                                        ),
                                                                    ]
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    className="mb-4",
                                ),
                                # Key metrics cards
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H5("Daily P&L"),
                                                                html.H3(
                                                                    id="daily-pnl",
                                                                    children="$0",
                                                                ),
                                                                html.P(
                                                                    id="daily-return",
                                                                    children="0%",
                                                                ),
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ],
                                            width=3,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H5("Weekly P&L"),
                                                                html.H3(
                                                                    id="weekly-pnl",
                                                                    children="$0",
                                                                ),
                                                                html.P(
                                                                    id="weekly-return",
                                                                    children="0%",
                                                                ),
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ],
                                            width=3,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H5("Sharpe Ratio"),
                                                                html.H3(
                                                                    id="sharpe-ratio",
                                                                    children="0.0",
                                                                ),
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ],
                                            width=3,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H5("Max Drawdown"),
                                                                html.H3(
                                                                    id="max-drawdown",
                                                                    children="0%",
                                                                ),
                                                            ]
                                                        )
                                                    ]
                                                )
                                            ],
                                            width=3,
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                        ),
                        # Positions Section
                        html.Div(
                            id="positions-section",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "Portfolio Positions"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                dcc.Graph(
                                                                    id="positions-pie-chart"
                                                                ),
                                                                html.Div(
                                                                    id="positions-table"
                                                                ),
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "Top Performers"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                dcc.Graph(
                                                                    id="top-performers-chart"
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "P&L Distribution"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                dcc.Graph(
                                                                    id="pnl-distribution-chart"
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    className="mb-4",
                                ),
                            ],
                        ),
                        # Performance Section
                        html.Div(
                            id="performance-section",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "Performance Metrics"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                dcc.Graph(
                                                                    id="performance-metrics-chart"
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    className="mb-4",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader("Risk Metrics"),
                                                        dbc.CardBody(
                                                            [
                                                                dcc.Graph(
                                                                    id="risk-metrics-chart"
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "Return Analysis"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                dcc.Graph(
                                                                    id="return-analysis-chart"
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                        ),
                        # Rebalancing Section
                        html.Div(
                            id="rebalancing-section",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            [
                                                                "Rebalancing Suggestions",
                                                                dbc.Button(
                                                                    "Refresh",
                                                                    id="refresh-rebalancing",
                                                                    size="sm",
                                                                    className="ms-2",
                                                                ),
                                                            ]
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                html.Div(
                                                                    id="rebalancing-suggestions"
                                                                ),
                                                                dcc.Graph(
                                                                    id="allocation-comparison-chart"
                                                                ),
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    className="mb-4",
                                )
                            ],
                        ),
                        # Tax Optimization Section
                        html.Div(
                            id="tax-section",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader("Tax Summary"),
                                                        dbc.CardBody(
                                                            [
                                                                html.Div(
                                                                    id="tax-summary"
                                                                ),
                                                                dcc.Graph(
                                                                    id="tax-breakdown-chart"
                                                                ),
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "Tax Loss Harvesting Opportunities"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                html.Div(
                                                                    id="harvesting-opportunities"
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-4",
                                )
                            ],
                        ),
                        # Transactions Section
                        html.Div(
                            id="transactions-section",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "Recent Transactions"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                html.Div(
                                                                    id="transactions-table"
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    className="mb-4",
                                )
                            ],
                        ),
                    ]
                ),
                # Hidden div for storing data
                html.Div(id="portfolio-data", style={"display": "none"}),
                # Interval component for auto-refresh
                dcc.Interval(
                    id="refresh-interval", interval=30000, n_intervals=0  # 30 seconds
                ),
            ]
        )

    def _setup_callbacks(self):
        """Setup Dash callbacks for interactivity."""

        @self.app.callback(
            [
                Output("portfolio-data", "children"),
                Output("total-value", "children"),
                Output("total-pnl", "children"),
                Output("total-positions", "children"),
                Output("total-return", "children"),
                Output("daily-pnl", "children"),
                Output("daily-return", "children"),
                Output("weekly-pnl", "children"),
                Output("weekly-return", "children"),
                Output("sharpe-ratio", "children"),
                Output("max-drawdown", "children"),
            ],
            [Input("refresh-interval", "n_intervals")],
        )
        async def update_overview(n_intervals):
            """Update portfolio overview data."""
            try:
                # Get portfolio data
                positions = await self.portfolio_manager.get_positions()
                performance = await self.portfolio_manager.get_performance_metrics()

                # Calculate overview metrics
                total_value = performance.total_value
                total_pnl = performance.total_pnl
                total_positions = len(positions)
                total_return = performance.total_return_percent

                # Format data for storage
                portfolio_data = {
                    "positions": [pos.__dict__ for pos in positions],
                    "performance": performance.__dict__,
                }

                return (
                    json.dumps(portfolio_data),
                    f"Total Value: ${total_value:,.2f}",
                    f"Total P&L: ${total_pnl:,.2f} ({total_return:+.2f}%)",
                    f"Positions: {total_positions}",
                    f"Total Return: {total_return:+.2f}%",
                    f"${performance.daily_pnl:,.2f}",
                    f"{performance.daily_return_percent:+.2f}%",
                    f"${performance.weekly_pnl:,.2f}",
                    f"{performance.weekly_return_percent:+.2f}%",
                    f"{performance.sharpe_ratio:.2f}",
                    f"{performance.max_drawdown:.2f}%",
                )

            except Exception as e:
                self.logger.error(f"Error updating overview: {e}")
                return (
                    json.dumps({}),
                    "Total Value: $0",
                    "Total P&L: $0 (0%)",
                    "Positions: 0",
                    "Total Return: 0%",
                    "$0",
                    "0%",
                    "$0",
                    "0%",
                    "0.0",
                    "0%",
                )

        @self.app.callback(
            [
                Output("positions-pie-chart", "figure"),
                Output("positions-table", "children"),
            ],
            [Input("portfolio-data", "children")],
        )
        def update_positions(portfolio_data):
            """Update positions visualization."""
            try:
                if not portfolio_data:
                    return self._create_empty_figure(), html.P("No data available")

                data = json.loads(portfolio_data)
                positions = data.get("positions", [])

                if not positions:
                    return self._create_empty_figure(), html.P("No positions available")

                # Create pie chart
                df = pd.DataFrame(positions)
                fig = px.pie(
                    df,
                    values="market_value",
                    names="symbol",
                    title="Portfolio Allocation by Market Value",
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")

                # Create positions table
                table_rows = []
                for pos in positions:
                    row = dbc.Row(
                        [
                            dbc.Col(pos["symbol"], width=2),
                            dbc.Col(f"{pos['quantity']:,.0f}", width=2),
                            dbc.Col(f"${pos['average_cost']:,.2f}", width=2),
                            dbc.Col(f"${pos['current_price']:,.2f}", width=2),
                            dbc.Col(f"${pos['market_value']:,.2f}", width=2),
                            dbc.Col(
                                (
                                    f"${pos['total_pnl']:,.2f} ({pos['total_pnl']/pos['cost_basis']*100:+.2f}%)"
                                    if pos["cost_basis"] > 0
                                    else "$0 (0%)"
                                ),
                                width=2,
                                className=(
                                    "text-success"
                                    if pos["total_pnl"] > 0
                                    else "text-danger"
                                ),
                            ),
                        ]
                    )
                    table_rows.append(row)

                table = html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col("Symbol", width=2, className="fw-bold"),
                                dbc.Col("Quantity", width=2, className="fw-bold"),
                                dbc.Col("Avg Cost", width=2, className="fw-bold"),
                                dbc.Col("Current Price", width=2, className="fw-bold"),
                                dbc.Col("Market Value", width=2, className="fw-bold"),
                                dbc.Col("Total P&L", width=2, className="fw-bold"),
                            ],
                            className="mb-2",
                        ),
                        *table_rows,
                    ]
                )

                return fig, table

            except Exception as e:
                self.logger.error(f"Error updating positions: {e}")
                return self._create_empty_figure(), html.P("Error loading positions")

        @self.app.callback(
            [
                Output("top-performers-chart", "figure"),
                Output("pnl-distribution-chart", "figure"),
            ],
            [Input("portfolio-data", "children")],
        )
        def update_performance_charts(portfolio_data):
            """Update performance charts."""
            try:
                if not portfolio_data:
                    return self._create_empty_figure(), self._create_empty_figure()

                data = json.loads(portfolio_data)
                positions = data.get("positions", [])

                if not positions:
                    return self._create_empty_figure(), self._create_empty_figure()

                df = pd.DataFrame(positions)

                # Top performers chart
                top_performers = df.nlargest(10, "total_pnl")
                fig1 = px.bar(
                    top_performers,
                    x="symbol",
                    y="total_pnl",
                    title="Top Performers by P&L",
                    color="total_pnl",
                    color_continuous_scale="RdYlGn",
                )
                fig1.update_layout(xaxis_tickangle=-45)

                # P&L distribution chart
                fig2 = px.histogram(
                    df,
                    x="total_pnl",
                    nbins=20,
                    title="P&L Distribution",
                    color_discrete_sequence=["lightblue"],
                )
                fig2.add_vline(x=0, line_dash="dash", line_color="red")

                return fig1, fig2

            except Exception as e:
                self.logger.error(f"Error updating performance charts: {e}")
                return self._create_empty_figure(), self._create_empty_figure()

        @self.app.callback(
            [
                Output("rebalancing-suggestions", "children"),
                Output("allocation-comparison-chart", "figure"),
            ],
            [
                Input("refresh-rebalancing", "n_clicks"),
                Input("portfolio-data", "children"),
            ],
        )
        async def update_rebalancing(n_clicks, portfolio_data):
            """Update rebalancing suggestions."""
            try:
                if not portfolio_data:
                    return html.P("No data available"), self._create_empty_figure()

                # Get rebalancing suggestions
                suggestions = await self.portfolio_manager.get_rebalancing_suggestions()

                if not suggestions:
                    return html.P("No rebalancing needed"), self._create_empty_figure()

                # Create suggestions table
                suggestion_rows = []
                for sug in suggestions:
                    row = dbc.Row(
                        [
                            dbc.Col(sug.symbol, width=2),
                            dbc.Col(f"{sug.current_allocation:.1%}", width=2),
                            dbc.Col(f"{sug.target_allocation:.1%}", width=2),
                            dbc.Col(sug.suggested_action.title(), width=2),
                            dbc.Col(f"{sug.suggested_quantity:,.0f}", width=2),
                            dbc.Col(
                                sug.priority.title(),
                                width=2,
                                className=f"text-{'danger' if sug.priority == 'high' else 'warning' if sug.priority == 'medium' else 'success'}",
                            ),
                        ]
                    )
                    suggestion_rows.append(row)

                suggestions_table = html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col("Symbol", width=2, className="fw-bold"),
                                dbc.Col("Current", width=2, className="fw-bold"),
                                dbc.Col("Target", width=2, className="fw-bold"),
                                dbc.Col("Action", width=2, className="fw-bold"),
                                dbc.Col("Quantity", width=2, className="fw-bold"),
                                dbc.Col("Priority", width=2, className="fw-bold"),
                            ],
                            className="mb-2",
                        ),
                        *suggestion_rows,
                    ]
                )

                # Create allocation comparison chart
                data = json.loads(portfolio_data)
                positions = data.get("positions", [])

                if positions:
                    df = pd.DataFrame(positions)
                    total_value = df["market_value"].sum()
                    df["current_allocation"] = df["market_value"] / total_value

                    # Get target allocations
                    target_allocations = self.portfolio_manager.target_allocations
                    df["target_allocation"] = (
                        df["symbol"].map(target_allocations).fillna(0)
                    )

                    # Create comparison chart
                    fig = go.Figure()

                    fig.add_trace(
                        go.Bar(
                            name="Current Allocation",
                            x=df["symbol"],
                            y=df["current_allocation"],
                            marker_color="lightblue",
                        )
                    )

                    fig.add_trace(
                        go.Bar(
                            name="Target Allocation",
                            x=df["symbol"],
                            y=df["target_allocation"],
                            marker_color="lightgreen",
                        )
                    )

                    fig.update_layout(
                        title="Current vs Target Allocations",
                        barmode="group",
                        xaxis_tickangle=-45,
                    )
                else:
                    fig = self._create_empty_figure()

                return suggestions_table, fig

            except Exception as e:
                self.logger.error(f"Error updating rebalancing: {e}")
                return (
                    html.P("Error loading rebalancing data"),
                    self._create_empty_figure(),
                )

        @self.app.callback(
            [
                Output("tax-summary", "children"),
                Output("tax-breakdown-chart", "figure"),
                Output("harvesting-opportunities", "children"),
            ],
            [Input("portfolio-data", "children")],
        )
        async def update_tax_optimization(portfolio_data):
            """Update tax optimization data."""
            try:
                # Get tax optimization data
                tax_opt = await self.portfolio_manager.get_tax_optimization()

                # Create tax summary
                summary = html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6("Short-term Gains"),
                                        html.P(
                                            f"${tax_opt.short_term_gains:,.2f}",
                                            className="text-success",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Long-term Gains"),
                                        html.P(
                                            f"${tax_opt.long_term_gains:,.2f}",
                                            className="text-success",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Short-term Losses"),
                                        html.P(
                                            f"${tax_opt.short_term_losses:,.2f}",
                                            className="text-danger",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Long-term Losses"),
                                        html.P(
                                            f"${tax_opt.long_term_losses:,.2f}",
                                            className="text-danger",
                                        ),
                                    ],
                                    width=3,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6("Net Capital Gains"),
                                        html.P(
                                            f"${tax_opt.net_capital_gains:,.2f}",
                                            className=(
                                                "text-success"
                                                if tax_opt.net_capital_gains > 0
                                                else "text-danger"
                                            ),
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Estimated Tax Liability"),
                                        html.P(f"${tax_opt.tax_liability:,.2f}"),
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                    ]
                )

                # Create tax breakdown chart
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=[
                                "Short-term Gains",
                                "Long-term Gains",
                                "Short-term Losses",
                                "Long-term Losses",
                            ],
                            values=[
                                float(tax_opt.short_term_gains),
                                float(tax_opt.long_term_gains),
                                float(tax_opt.short_term_losses),
                                float(tax_opt.long_term_losses),
                            ],
                            hole=0.3,
                        )
                    ]
                )
                fig.update_layout(title="Tax Breakdown")

                # Create harvesting opportunities
                if tax_opt.harvesting_opportunities:
                    opportunity_rows = []
                    for opp in tax_opt.harvesting_opportunities:
                        row = dbc.Row(
                            [
                                dbc.Col(opp["symbol"], width=3),
                                dbc.Col(f"${opp['unrealized_loss']:,.2f}", width=3),
                                dbc.Col(f"{opp['quantity']:,.0f}", width=2),
                                dbc.Col(
                                    f"${opp['estimated_tax_savings']:,.2f}", width=4
                                ),
                            ]
                        )
                        opportunity_rows.append(row)

                    opportunities = html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col("Symbol", width=3, className="fw-bold"),
                                    dbc.Col(
                                        "Unrealized Loss", width=3, className="fw-bold"
                                    ),
                                    dbc.Col("Quantity", width=2, className="fw-bold"),
                                    dbc.Col(
                                        "Est. Tax Savings", width=4, className="fw-bold"
                                    ),
                                ],
                                className="mb-2",
                            ),
                            *opportunity_rows,
                        ]
                    )
                else:
                    opportunities = html.P(
                        "No tax loss harvesting opportunities available"
                    )

                return summary, fig, opportunities

            except Exception as e:
                self.logger.error(f"Error updating tax optimization: {e}")
                return (
                    html.P("Error loading tax data"),
                    self._create_empty_figure(),
                    html.P("Error loading opportunities"),
                )

        @self.app.callback(
            Output("transactions-table", "children"),
            [Input("portfolio-data", "children")],
        )
        async def update_transactions(portfolio_data):
            """Update transactions table."""
            try:
                # Get recent transactions
                transactions = await self.portfolio_manager.get_transactions(limit=20)

                if not transactions:
                    return html.P("No transactions available")

                # Create transactions table
                transaction_rows = []
                for tx in transactions:
                    row = dbc.Row(
                        [
                            dbc.Col(tx.symbol, width=2),
                            dbc.Col(tx.transaction_type.value.title(), width=2),
                            dbc.Col(f"{tx.quantity:,.0f}", width=2),
                            dbc.Col(f"${tx.price:,.2f}", width=2),
                            dbc.Col(f"${tx.commission:,.2f}", width=2),
                            dbc.Col(tx.timestamp.strftime("%Y-%m-%d %H:%M"), width=2),
                        ]
                    )
                    transaction_rows.append(row)

                table = html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col("Symbol", width=2, className="fw-bold"),
                                dbc.Col("Type", width=2, className="fw-bold"),
                                dbc.Col("Quantity", width=2, className="fw-bold"),
                                dbc.Col("Price", width=2, className="fw-bold"),
                                dbc.Col("Commission", width=2, className="fw-bold"),
                                dbc.Col("Date", width=2, className="fw-bold"),
                            ],
                            className="mb-2",
                        ),
                        *transaction_rows,
                    ]
                )

                return table

            except Exception as e:
                self.logger.error(f"Error updating transactions: {e}")
                return html.P("Error loading transactions")

    def _create_empty_figure(self) -> go.Figure:
        """Create an empty figure for error cases."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    def run(self, host: str = "0.0.0.0", port: int = 8050, debug: bool = False):
        """Run the dashboard."""
        self.app.run_server(host=host, port=port, debug=debug)
