"""
Alert Dashboard Module

This module provides a simple alert dashboard component that can be
integrated into the main web dashboard for managing alerts.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Any
import requests
import json

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertDashboard:
    """
    Alert Dashboard Component

    Provides a web interface for managing alert conditions and viewing alert events.
    """

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.logger = logger

    def create_layout(self) -> html.Div:
        """
        Create the main alert dashboard layout

        Returns:
            Dash layout component
        """
        return html.Div(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2("Alert Management Dashboard", className="mb-3"),
                                html.P(
                                    "Monitor and manage stock market alerts",
                                    className="text-muted",
                                ),
                            ]
                        )
                    ]
                ),
                # Statistics Cards
                dbc.Row(
                    [
                        dbc.Col(
                            self._create_stat_card(
                                "Total Conditions", "total_conditions", "primary"
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            self._create_stat_card(
                                "Active Conditions", "enabled_conditions", "success"
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            self._create_stat_card(
                                "Total Events", "total_events", "warning"
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            self._create_stat_card(
                                "Pending Events", "pending_events", "danger"
                            ),
                            width=3,
                        ),
                    ],
                    className="mb-4",
                ),
                # Main Content Tabs
                dbc.Tabs(
                    [
                        # Alert Conditions Tab
                        dbc.Tab(
                            [self._create_conditions_tab()],
                            label="Alert Conditions",
                            tab_id="conditions",
                        ),
                        # Alert Events Tab
                        dbc.Tab(
                            [self._create_events_tab()],
                            label="Alert Events",
                            tab_id="events",
                        ),
                        # Statistics Tab
                        dbc.Tab(
                            [self._create_statistics_tab()],
                            label="Statistics",
                            tab_id="statistics",
                        ),
                        # Settings Tab
                        dbc.Tab(
                            [self._create_settings_tab()],
                            label="Settings",
                            tab_id="settings",
                        ),
                    ],
                    id="alert-tabs",
                    active_tab="conditions",
                ),
                # Hidden divs for storing data
                dcc.Store(id="alert-conditions-store"),
                dcc.Store(id="alert-events-store"),
                dcc.Store(id="alert-statistics-store"),
                # Interval component for auto-refresh
                dcc.Interval(
                    id="alert-refresh-interval",
                    interval=30000,  # 30 seconds
                    n_intervals=0,
                ),
                # Modal for creating/editing alerts
                self._create_alert_modal(),
                # Toast notifications
                dbc.Toast(
                    id="alert-toast",
                    header="Alert Notification",
                    is_open=False,
                    dismissable=True,
                    duration=4000,
                    icon="primary",
                ),
            ]
        )

    def _create_stat_card(self, title: str, data_key: str, color: str) -> dbc.Card:
        """Create a statistics card"""
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4(
                            id=f"stat-{data_key}",
                            children="0",
                            className=f"text-{color}",
                        ),
                        html.P(title, className="card-text text-muted"),
                    ]
                )
            ]
        )

    def _create_conditions_tab(self) -> html.Div:
        """Create the alert conditions tab"""
        return html.Div(
            [
                # Controls
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Add New Alert",
                                    id="add-alert-btn",
                                    color="primary",
                                    className="me-2",
                                ),
                                dbc.Button(
                                    "Refresh",
                                    id="refresh-conditions-btn",
                                    color="secondary",
                                    className="me-2",
                                ),
                                dbc.Switch(
                                    id="monitoring-switch",
                                    label="Enable Monitoring",
                                    className="me-2",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dcc.Dropdown(
                                    id="symbol-filter",
                                    placeholder="Filter by symbol...",
                                    multi=True,
                                    className="float-end",
                                )
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                # Conditions Table
                dbc.Table(
                    [
                        html.Thead(
                            [
                                html.Tr(
                                    [
                                        html.Th("Symbol"),
                                        html.Th("Type"),
                                        html.Th("Condition"),
                                        html.Th("Threshold"),
                                        html.Th("Severity"),
                                        html.Th("Status"),
                                        html.Th("Actions"),
                                    ]
                                )
                            ]
                        ),
                        html.Tbody(id="conditions-table-body"),
                    ],
                    id="conditions-table",
                    striped=True,
                    bordered=True,
                    hover=True,
                ),
            ]
        )

    def _create_events_tab(self) -> html.Div:
        """Create the alert events tab"""
        return html.Div(
            [
                # Controls
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Refresh",
                                    id="refresh-events-btn",
                                    color="secondary",
                                    className="me-2",
                                ),
                                dcc.DatePickerRange(
                                    id="events-date-range",
                                    start_date=(
                                        datetime.now() - timedelta(days=7)
                                    ).date(),
                                    end_date=datetime.now().date(),
                                    className="me-2",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dcc.Dropdown(
                                    id="events-symbol-filter",
                                    placeholder="Filter by symbol...",
                                    multi=True,
                                    className="float-end",
                                )
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                # Events Table
                dbc.Table(
                    [
                        html.Thead(
                            [
                                html.Tr(
                                    [
                                        html.Th("Time"),
                                        html.Th("Symbol"),
                                        html.Th("Type"),
                                        html.Th("Severity"),
                                        html.Th("Message"),
                                        html.Th("Status"),
                                        html.Th("Actions"),
                                    ]
                                )
                            ]
                        ),
                        html.Tbody(id="events-table-body"),
                    ],
                    id="events-table",
                    striped=True,
                    bordered=True,
                    hover=True,
                ),
            ]
        )

    def _create_statistics_tab(self) -> html.Div:
        """Create the statistics tab"""
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col([dcc.Graph(id="severity-distribution-chart")], width=6),
                        dbc.Col([dcc.Graph(id="type-distribution-chart")], width=6),
                    ],
                    className="mb-4",
                ),
                dbc.Row([dbc.Col([dcc.Graph(id="events-timeline-chart")], width=12)]),
            ]
        )

    def _create_settings_tab(self) -> html.Div:
        """Create the settings tab"""
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Notification Settings"),
                                        dbc.CardBody(
                                            [
                                                dbc.Form(
                                                    [
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Email Notifications"
                                                                        ),
                                                                        dbc.Switch(
                                                                            id="email-notifications",
                                                                            label="Enable",
                                                                            value=True,
                                                                        ),
                                                                    ],
                                                                    width=6,
                                                                ),
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Telegram Notifications"
                                                                        ),
                                                                        dbc.Switch(
                                                                            id="telegram-notifications",
                                                                            label="Enable",
                                                                            value=False,
                                                                        ),
                                                                    ],
                                                                    width=6,
                                                                ),
                                                            ],
                                                            className="mb-3",
                                                        ),
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Slack Notifications"
                                                                        ),
                                                                        dbc.Switch(
                                                                            id="slack-notifications",
                                                                            label="Enable",
                                                                            value=False,
                                                                        ),
                                                                    ],
                                                                    width=6,
                                                                ),
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Webhook Notifications"
                                                                        ),
                                                                        dbc.Switch(
                                                                            id="webhook-notifications",
                                                                            label="Enable",
                                                                            value=False,
                                                                        ),
                                                                    ],
                                                                    width=6,
                                                                ),
                                                            ],
                                                            className="mb-3",
                                                        ),
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Default Cooldown (minutes)"
                                                                        ),
                                                                        dbc.Input(
                                                                            id="default-cooldown",
                                                                            type="number",
                                                                            value=30,
                                                                            min=1,
                                                                        ),
                                                                    ],
                                                                    width=6,
                                                                ),
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Auto-refresh Interval (seconds)"
                                                                        ),
                                                                        dbc.Input(
                                                                            id="refresh-interval",
                                                                            type="number",
                                                                            value=30,
                                                                            min=5,
                                                                        ),
                                                                    ],
                                                                    width=6,
                                                                ),
                                                            ]
                                                        ),
                                                    ]
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
                                        dbc.CardHeader("Test Notifications"),
                                        dbc.CardBody(
                                            [
                                                dbc.Form(
                                                    [
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Symbol"
                                                                        ),
                                                                        dbc.Input(
                                                                            id="test-symbol",
                                                                            placeholder="AAPL",
                                                                            value="AAPL",
                                                                        ),
                                                                    ],
                                                                    width=4,
                                                                ),
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Alert Type"
                                                                        ),
                                                                        dcc.Dropdown(
                                                                            id="test-alert-type",
                                                                            options=[
                                                                                {
                                                                                    "label": "Price Threshold",
                                                                                    "value": "price_threshold",
                                                                                },
                                                                                {
                                                                                    "label": "Price Change",
                                                                                    "value": "price_change",
                                                                                },
                                                                                {
                                                                                    "label": "Volume Spike",
                                                                                    "value": "volume_spike",
                                                                                },
                                                                                {
                                                                                    "label": "Anomaly Detected",
                                                                                    "value": "anomaly_detected",
                                                                                },
                                                                            ],
                                                                            value="price_threshold",
                                                                        ),
                                                                    ],
                                                                    width=4,
                                                                ),
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "Notification Method"
                                                                        ),
                                                                        dcc.Dropdown(
                                                                            id="test-notification-method",
                                                                            options=[
                                                                                {
                                                                                    "label": "Email",
                                                                                    "value": "email",
                                                                                },
                                                                                {
                                                                                    "label": "Telegram",
                                                                                    "value": "telegram",
                                                                                },
                                                                                {
                                                                                    "label": "Slack",
                                                                                    "value": "slack",
                                                                                },
                                                                                {
                                                                                    "label": "Webhook",
                                                                                    "value": "webhook",
                                                                                },
                                                                            ],
                                                                            value="email",
                                                                        ),
                                                                    ],
                                                                    width=4,
                                                                ),
                                                            ],
                                                            className="mb-3",
                                                        ),
                                                        dbc.Button(
                                                            "Send Test Notification",
                                                            id="test-notification-btn",
                                                            color="warning",
                                                        ),
                                                    ]
                                                )
                                            ]
                                        ),
                                    ]
                                )
                            ],
                            width=6,
                        ),
                    ]
                )
            ]
        )

    def _create_alert_modal(self) -> dbc.Modal:
        """Create the alert creation/editing modal"""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
                dbc.ModalBody(
                    [
                        dbc.Form(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Symbol"),
                                                dbc.Input(
                                                    id="modal-symbol",
                                                    type="text",
                                                    placeholder="AAPL",
                                                ),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Alert Type"),
                                                dcc.Dropdown(
                                                    id="modal-alert-type",
                                                    options=[
                                                        {
                                                            "label": "Price Threshold",
                                                            "value": "price_threshold",
                                                        },
                                                        {
                                                            "label": "Price Change",
                                                            "value": "price_change",
                                                        },
                                                        {
                                                            "label": "Technical Indicator",
                                                            "value": "technical_indicator",
                                                        },
                                                        {
                                                            "label": "Volume Spike",
                                                            "value": "volume_spike",
                                                        },
                                                        {
                                                            "label": "Anomaly Detected",
                                                            "value": "anomaly_detected",
                                                        },
                                                    ],
                                                ),
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Condition"),
                                                dbc.Input(
                                                    id="modal-condition",
                                                    type="text",
                                                    placeholder="price > 100",
                                                ),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Threshold"),
                                                dbc.Input(
                                                    id="modal-threshold",
                                                    type="number",
                                                    step="0.01",
                                                ),
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Severity"),
                                                dcc.Dropdown(
                                                    id="modal-severity",
                                                    options=[
                                                        {
                                                            "label": "Info",
                                                            "value": "info",
                                                        },
                                                        {
                                                            "label": "Warning",
                                                            "value": "warning",
                                                        },
                                                        {
                                                            "label": "Critical",
                                                            "value": "critical",
                                                        },
                                                    ],
                                                    value="warning",
                                                ),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Cooldown (minutes)"),
                                                dbc.Input(
                                                    id="modal-cooldown",
                                                    type="number",
                                                    value=30,
                                                    min=1,
                                                ),
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Notification Methods"),
                                                dcc.Checklist(
                                                    id="modal-notification-methods",
                                                    options=[
                                                        {
                                                            "label": "Email",
                                                            "value": "email",
                                                        },
                                                        {
                                                            "label": "Telegram",
                                                            "value": "telegram",
                                                        },
                                                        {
                                                            "label": "Slack",
                                                            "value": "slack",
                                                        },
                                                        {
                                                            "label": "Webhook",
                                                            "value": "webhook",
                                                        },
                                                    ],
                                                    value=["email"],
                                                ),
                                            ],
                                            width=12,
                                        )
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Custom Message (optional)"),
                                                dbc.Textarea(
                                                    id="modal-custom-message",
                                                    placeholder="Custom alert message...",
                                                ),
                                            ],
                                            width=12,
                                        )
                                    ]
                                ),
                            ]
                        )
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button("Cancel", id="modal-cancel", className="ms-auto"),
                        dbc.Button("Save", id="modal-save", color="primary"),
                    ]
                ),
            ],
            id="alert-modal",
            size="lg",
            is_open=False,
        )

    def register_callbacks(self, app: dash.Dash):
        """Register all callbacks for the alert dashboard"""

        @app.callback(
            [
                Output("alert-conditions-store", "data"),
                Output("alert-events-store", "data"),
                Output("alert-statistics-store", "data"),
            ],
            [
                Input("alert-refresh-interval", "n_intervals"),
                Input("refresh-conditions-btn", "n_clicks"),
                Input("refresh-events-btn", "n_clicks"),
            ],
        )
        def refresh_data(n_intervals, refresh_conditions, refresh_events):
            """Refresh alert data"""
            try:
                # Get conditions
                conditions_response = requests.get(
                    f"{self.api_base_url}/alerts/conditions"
                )
                conditions = (
                    conditions_response.json()
                    if conditions_response.status_code == 200
                    else []
                )

                # Get events
                events_response = requests.get(f"{self.api_base_url}/alerts/events")
                events = (
                    events_response.json() if events_response.status_code == 200 else []
                )

                # Get statistics
                stats_response = requests.get(f"{self.api_base_url}/alerts/statistics")
                stats = (
                    stats_response.json() if stats_response.status_code == 200 else {}
                )

                return conditions, events, stats

            except Exception as e:
                self.logger.error(f"Error refreshing data: {e}")
                return [], [], {}

        @app.callback(
            [
                Output("stat-total_conditions", "children"),
                Output("stat-enabled_conditions", "children"),
                Output("stat-total_events", "children"),
                Output("stat-pending_events", "children"),
            ],
            [Input("alert-statistics-store", "data")],
        )
        def update_statistics(stats_data):
            """Update statistics cards"""
            if not stats_data:
                return "0", "0", "0", "0"

            return (
                str(stats_data.get("total_conditions", 0)),
                str(stats_data.get("enabled_conditions", 0)),
                str(stats_data.get("total_events", 0)),
                str(stats_data.get("pending_events", 0)),
            )

        @app.callback(
            Output("conditions-table-body", "children"),
            [Input("alert-conditions-store", "data"), Input("symbol-filter", "value")],
        )
        def update_conditions_table(conditions_data, symbol_filter):
            """Update conditions table"""
            if not conditions_data:
                return []

            # Filter by symbol if specified
            if symbol_filter:
                conditions_data = [
                    c for c in conditions_data if c["symbol"] in symbol_filter
                ]

            rows = []
            for condition in conditions_data:
                status_badge = dbc.Badge(
                    "Active" if condition["enabled"] else "Disabled",
                    color="success" if condition["enabled"] else "secondary",
                )

                severity_badge = dbc.Badge(
                    condition["severity"].title(),
                    color={
                        "info": "info",
                        "warning": "warning",
                        "critical": "danger",
                    }.get(condition["severity"], "secondary"),
                )

                actions = html.Div(
                    [
                        dbc.Button(
                            "Edit", size="sm", color="primary", className="me-1"
                        ),
                        dbc.Button("Delete", size="sm", color="danger"),
                    ]
                )

                rows.append(
                    html.Tr(
                        [
                            html.Td(condition["symbol"]),
                            html.Td(condition["alert_type"].replace("_", " ").title()),
                            html.Td(condition["condition"]),
                            html.Td(f"{condition['threshold']:.2f}"),
                            html.Td(severity_badge),
                            html.Td(status_badge),
                            html.Td(actions),
                        ]
                    )
                )

            return rows

        @app.callback(
            Output("events-table-body", "children"),
            [
                Input("alert-events-store", "data"),
                Input("events-symbol-filter", "value"),
                Input("events-date-range", "start_date"),
                Input("events-date-range", "end_date"),
            ],
        )
        def update_events_table(events_data, symbol_filter, start_date, end_date):
            """Update events table"""
            if not events_data:
                return []

            # Filter by symbol if specified
            if symbol_filter:
                events_data = [e for e in events_data if e["symbol"] in symbol_filter]

            # Filter by date range if specified
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                events_data = [
                    e
                    for e in events_data
                    if start_dt
                    <= datetime.fromisoformat(e["triggered_at"].replace("Z", "+00:00"))
                    <= end_dt
                ]

            rows = []
            for event in events_data:
                time_str = datetime.fromisoformat(
                    event["triggered_at"].replace("Z", "+00:00")
                ).strftime("%Y-%m-%d %H:%M:%S")

                severity_badge = dbc.Badge(
                    event["severity"].title(),
                    color={
                        "info": "info",
                        "warning": "warning",
                        "critical": "danger",
                    }.get(event["severity"], "secondary"),
                )

                status_badge = dbc.Badge(
                    "Acknowledged" if event["acknowledged"] else "Pending",
                    color="success" if event["acknowledged"] else "warning",
                )

                actions = html.Div(
                    [
                        (
                            dbc.Button(
                                "Acknowledge",
                                size="sm",
                                color="success",
                                className="me-1",
                            )
                            if not event["acknowledged"]
                            else html.Span("")
                        ),
                        dbc.Button("View", size="sm", color="info"),
                    ]
                )

                rows.append(
                    html.Tr(
                        [
                            html.Td(time_str),
                            html.Td(event["symbol"]),
                            html.Td(event["alert_type"].replace("_", " ").title()),
                            html.Td(severity_badge),
                            html.Td(
                                event["message"][:50] + "..."
                                if len(event["message"]) > 50
                                else event["message"]
                            ),
                            html.Td(status_badge),
                            html.Td(actions),
                        ]
                    )
                )

            return rows

        @app.callback(
            [
                Output("severity-distribution-chart", "figure"),
                Output("type-distribution-chart", "figure"),
            ],
            [Input("alert-statistics-store", "data")],
        )
        def update_charts(stats_data):
            """Update statistics charts"""
            if not stats_data:
                return {}, {}

            # Severity distribution pie chart
            severity_data = stats_data.get("severity_distribution", {})
            severity_fig = px.pie(
                values=list(severity_data.values()),
                names=list(severity_data.keys()),
                title="Alert Events by Severity",
            )

            # Type distribution bar chart
            type_data = stats_data.get("type_distribution", {})
            type_fig = px.bar(
                x=list(type_data.keys()),
                y=list(type_data.values()),
                title="Alert Events by Type",
            )

            return severity_fig, type_fig

        @app.callback(
            [Output("alert-modal", "is_open"), Output("modal-title", "children")],
            [
                Input("add-alert-btn", "n_clicks"),
                Input("modal-cancel", "n_clicks"),
                Input("modal-save", "n_clicks"),
            ],
            [State("alert-modal", "is_open")],
        )
        def toggle_modal(add_clicks, cancel_clicks, save_clicks, is_open):
            """Toggle alert modal"""
            if add_clicks or cancel_clicks or save_clicks:
                return not is_open, "Add New Alert"
            return is_open, "Add New Alert"

        @app.callback(
            Output("alert-toast", "is_open"),
            [Input("modal-save", "n_clicks")],
            [
                State("modal-symbol", "value"),
                State("modal-alert-type", "value"),
                State("modal-condition", "value"),
                State("modal-threshold", "value"),
                State("modal-severity", "value"),
                State("modal-cooldown", "value"),
                State("modal-notification-methods", "value"),
                State("modal-custom-message", "value"),
            ],
        )
        def save_alert(
            save_clicks,
            symbol,
            alert_type,
            condition,
            threshold,
            severity,
            cooldown,
            notification_methods,
            custom_message,
        ):
            """Save new alert condition"""
            if not save_clicks:
                return False

            try:
                # Create alert condition
                alert_data = {
                    "symbol": symbol,
                    "alert_type": alert_type,
                    "condition": condition,
                    "threshold": threshold,
                    "severity": severity,
                    "enabled": True,
                    "cooldown_minutes": cooldown,
                    "notification_methods": notification_methods,
                    "custom_message": custom_message,
                }

                response = requests.post(
                    f"{self.api_base_url}/alerts/conditions", json=alert_data
                )

                if response.status_code == 200:
                    return True  # Show success toast
                else:
                    return False

            except Exception as e:
                self.logger.error(f"Error saving alert: {e}")
                return False

        @app.callback(
            Output("monitoring-switch", "value"), [Input("monitoring-switch", "value")]
        )
        def toggle_monitoring(value):
            """Toggle alert monitoring"""
            try:
                if value:
                    response = requests.post(
                        f"{self.api_base_url}/alerts/monitoring/start"
                    )
                else:
                    response = requests.post(
                        f"{self.api_base_url}/alerts/monitoring/stop"
                    )

                return value

            except Exception as e:
                self.logger.error(f"Error toggling monitoring: {e}")
                return not value

        @app.callback(
            Output("alert-toast", "children"),
            [Input("test-notification-btn", "n_clicks")],
            [
                State("test-symbol", "value"),
                State("test-alert-type", "value"),
                State("test-notification-method", "value"),
            ],
        )
        def test_notification(test_clicks, symbol, alert_type, notification_method):
            """Test notification delivery"""
            if not test_clicks:
                return ""

            try:
                response = requests.post(
                    f"{self.api_base_url}/alerts/test-notification",
                    params={
                        "symbol": symbol,
                        "alert_type": alert_type,
                        "notification_method": notification_method,
                    },
                )

                if response.status_code == 200:
                    return "Test notification sent successfully!"
                else:
                    return "Failed to send test notification"

            except Exception as e:
                self.logger.error(f"Error testing notification: {e}")
                return "Error sending test notification"


def create_alert_dashboard(
    api_base_url: str = "http://localhost:8080",
) -> AlertDashboard:
    """
    Create an alert dashboard instance

    Args:
        api_base_url: Base URL for the API

    Returns:
        AlertDashboard instance
    """
    return AlertDashboard(api_base_url)
