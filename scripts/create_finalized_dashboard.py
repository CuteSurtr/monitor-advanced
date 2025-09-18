#!/usr/bin/env python3
"""
Create Macroeconomics Dashboard - Finalized
Combines ALL working dashboards and tiles into one comprehensive dashboard
"""

import json
from datetime import datetime

def create_finalized_dashboard():
    """Create the comprehensive finalized macro dashboard with everything"""
    
    dashboard = {
        "id": None,
        "title": "Macroeconomics Dashboard - Finalized",
        "tags": ["macro", "economics", "finalized", "comprehensive"],
        "style": "dark",
        "timezone": "browser",
        "refresh": "30s",
        "time": {
            "from": "now-90d",
            "to": "now"
        },
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
        },
        "panels": [],
        "schemaVersion": 37,
        "version": 1,
        "annotations": {"list": []},
        "templating": {"list": []}
    }
    
    panel_id = 1
    y_pos = 0
    
    # === TREASURY & YIELD CURVES ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "TREASURY & YIELD CURVES",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## TREASURY & YIELD CURVES", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Treasury Yield Curve
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Treasury Yield Curve",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "treasury_yield_curve")
  |> keep(columns: ["_time", "_value", "maturity"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 10},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.maturity}",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # 10Y-2Y Yield Curve Spread
    dashboard["panels"].append({
        "id": panel_id,
        "title": "10Y-2Y Yield Spread",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
data_2y = from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "treasury_yield_curve" and r.maturity == "2Y")
  |> keep(columns: ["_time", "_value"])
  |> rename(columns: {_value: "yield_2y"})

data_10y = from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "treasury_yield_curve" and r.maturity == "10Y")
  |> keep(columns: ["_time", "_value"])
  |> rename(columns: {_value: "yield_10y"})

join(tables: {t1: data_2y, t2: data_10y}, on: ["_time"])
  |> map(fn: (r) => ({r with _value: r.yield_10y - r.yield_2y, _field: "spread"}))
  |> keep(columns: ["_time", "_value", "_field"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "10Y-2Y Spread",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === LABOR MARKET & INFLATION ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "LABOR MARKET & INFLATION",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## LABOR MARKET & INFLATION", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Labor Market
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Labor Market",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bls_economic_data")
  |> filter(fn: (r) => r.indicator == "unemployment_rate" or r.indicator == "nfp" or r.indicator == "jobless_claims")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "unemployment_rate"}, "properties": [{"id": "displayName", "value": "Unemployment %"}]},
                {"matcher": {"id": "byName", "options": "nfp"}, "properties": [{"id": "displayName", "value": "NFP (000s)"}]},
                {"matcher": {"id": "byName", "options": "jobless_claims"}, "properties": [{"id": "displayName", "value": "Claims (000s)"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Inflation
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Inflation",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bls_economic_data")
  |> filter(fn: (r) => r.indicator == "cpi" or r.indicator == "core_cpi" or r.indicator == "ppi")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}",
                "unit": "percent"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "cpi"}, "properties": [{"id": "displayName", "value": "CPI"}]},
                {"matcher": {"id": "byName", "options": "core_cpi"}, "properties": [{"id": "displayName", "value": "Core CPI"}]},
                {"matcher": {"id": "byName", "options": "ppi"}, "properties": [{"id": "displayName", "value": "PPI"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Fed Funds Rate
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Fed Funds Rate",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "fred_rates")
  |> filter(fn: (r) => r.rate_type == "fed_funds")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "Fed Funds Rate",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === GDP & ECONOMIC ACTIVITY ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "GDP & ECONOMIC ACTIVITY",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## GDP & ECONOMIC ACTIVITY", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # GDP Growth
    dashboard["panels"].append({
        "id": panel_id,
        "title": "GDP Growth",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bea_economic_data")
  |> filter(fn: (r) => r.indicator == "gdp")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "GDP Growth %",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Industrial Production
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Industrial Production",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bea_economic_data")
  |> filter(fn: (r) => r.indicator == "industrial_production")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "Industrial Production %",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Retail Sales
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Retail Sales",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "census_economic_data")
  |> filter(fn: (r) => r.indicator == "retail_sales")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "Retail Sales",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === HOUSING & REAL ESTATE ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "HOUSING & REAL ESTATE",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## HOUSING & REAL ESTATE", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Housing Activity
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Housing Activity",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "housing_data")
  |> filter(fn: (r) => r.indicator == "housing_starts" or r.indicator == "building_permits")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "housing_starts"}, "properties": [{"id": "displayName", "value": "Housing Starts"}]},
                {"matcher": {"id": "byName", "options": "building_permits"}, "properties": [{"id": "displayName", "value": "Building Permits"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Home Prices & Mortgage Rates
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Home Prices & Mortgage Rates",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "housing_data")
  |> filter(fn: (r) => r.indicator == "case_shiller_index" or r.indicator == "mortgage_rates")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "case_shiller_index"}, "properties": [{"id": "displayName", "value": "Home Prices"}]},
                {"matcher": {"id": "byName", "options": "mortgage_rates"}, "properties": [{"id": "displayName", "value": "Mortgage Rates"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Home Sales
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Home Sales",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "housing_data")
  |> filter(fn: (r) => r.indicator == "existing_home_sales")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "Home Sales"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === ENERGY & COMMODITIES ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "ENERGY & COMMODITIES",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## ENERGY & COMMODITIES", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Energy Fundamentals
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Energy Fundamentals",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "commodity_data")
  |> filter(fn: (r) => r.indicator == "oil_inventories" or r.indicator == "gasoline_prices" or r.indicator == "natural_gas_storage")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "oil_inventories"}, "properties": [{"id": "displayName", "value": "Oil Inventories"}]},
                {"matcher": {"id": "byName", "options": "gasoline_prices"}, "properties": [{"id": "displayName", "value": "Gasoline Prices"}]},
                {"matcher": {"id": "byName", "options": "natural_gas_storage"}, "properties": [{"id": "displayName", "value": "Natural Gas Storage"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Commodity Index
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Commodity Index",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "commodity_data")
  |> filter(fn: (r) => r.indicator == "commodity_index")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "Commodity Index"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === FINANCIAL CONDITIONS & VOLATILITY ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "FINANCIAL CONDITIONS & VOLATILITY",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## FINANCIAL CONDITIONS & VOLATILITY", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Market Volatility
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Market Volatility",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "market_data" and r.indicator == "vix")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "VIX",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Credit Spreads
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Credit Spreads",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "advanced_financial" and r.indicator == "cds_spreads")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "CDS Spreads",
                "unit": "basis points"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # SOFR & Repo Markets
    dashboard["panels"].append({
        "id": panel_id,
        "title": "SOFR & Repo Markets",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "fred_rates")
  |> filter(fn: (r) => r.rate_type == "sofr")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "SOFR",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === BANKING & LIQUIDITY METRICS ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "BANKING & LIQUIDITY METRICS",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## BANKING & LIQUIDITY METRICS", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Money Supply (M1/M2)
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Money Supply (M1/M2)",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "banking_data")
  |> filter(fn: (r) => r.indicator == "m1_money_supply" or r.indicator == "m2_money_supply")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "m1_money_supply"}, "properties": [{"id": "displayName", "value": "M1 Money Supply"}]},
                {"matcher": {"id": "byName", "options": "m2_money_supply"}, "properties": [{"id": "displayName", "value": "M2 Money Supply"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Bank Assets
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Bank Assets",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "banking_data")
  |> filter(fn: (r) => r.indicator == "bank_assets")
  |> keep(columns: ["_time", "_value"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "Bank Assets"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === BUSINESS & CONSUMER CONFIDENCE ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "BUSINESS & CONSUMER CONFIDENCE",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## BUSINESS & CONSUMER CONFIDENCE", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Business Confidence & Consumer Confidence
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Business & Consumer Confidence",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => 
    (r._measurement == "business_confidence" and (r.indicator == "ism_pmi" or r.indicator == "nfib_optimism")) or
    (r._measurement == "consumer_data" and r.indicator == "consumer_confidence"))
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "ism_pmi"}, "properties": [{"id": "displayName", "value": "ISM PMI"}]},
                {"matcher": {"id": "byName", "options": "nfib_optimism"}, "properties": [{"id": "displayName", "value": "NFIB Optimism"}]},
                {"matcher": {"id": "byName", "options": "consumer_confidence"}, "properties": [{"id": "displayName", "value": "Consumer Confidence"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Trade Balance & Current Account
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Trade Balance & Current Account",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "trade_data")
  |> filter(fn: (r) => r.indicator == "trade_balance" or r.indicator == "current_account")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "trade_balance"}, "properties": [{"id": "displayName", "value": "Trade Balance"}]},
                {"matcher": {"id": "byName", "options": "current_account"}, "properties": [{"id": "displayName", "value": "Current Account"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    return dashboard

def main():
    print("Creating Macroeconomics Dashboard - Finalized")
    print("=" * 50)
    print("Combining ALL working dashboards and tiles:")
    print("* Treasury Yield Curve & 10Y-2Y Spread")
    print("* Labor Market & Inflation")
    print("* Fed Funds Rate")
    print("* GDP & Economic Activity")
    print("* Housing & Real Estate Activity")
    print("* Energy & Commodities")
    print("* Financial Conditions & Market Volatility")
    print("* SOFR & Repo Markets")
    print("* Banking & Liquidity Metrics (M1/M2, Bank Assets)")
    print("* Business & Consumer Confidence")
    print("* Trade Balance & Current Account")
    print("* Macro-only focus (no market data tables)")
    
    dashboard = create_finalized_dashboard()
    
    # Write dashboard file
    output_file = "grafana/provisioning/dashboards/macroeconomics_dashboard_finalized.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\nDashboard created: {output_file}")
    print("\nFEATURES:")
    print("* Complete macro economic monitoring only")
    print("* Professional institutional-grade layout")
    print("* Pure InfluxDB macro data source")
    print("* Clean legend labels throughout")
    print("* No market data - pure macroeconomics focus")
    
    print("\nNext: Restart Grafana to load the finalized dashboard")

if __name__ == "__main__":
    main()