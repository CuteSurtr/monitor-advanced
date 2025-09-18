#!/usr/bin/env python3
"""
Create Complete Professional Dashboard with ALL Requested Indicators
Includes all indicators requested: CPI, PPI, Core CPI, Unemployment, NFP, etc.
"""

import json
from datetime import datetime

def create_complete_dashboard():
    """Create dashboard with ALL requested indicators and clean legends"""
    
    dashboard = {
        "id": None,
        "title": "Complete Professional Macro Dashboard",
        "tags": ["macro", "economics", "professional", "complete"],
        "style": "dark",
        "timezone": "browser",
        "refresh": "5m",
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
    
    # === INFLATION & PRICES ===
    dashboard["panels"].extend([
        # Section Header
        {
            "id": panel_id,
            "title": "INFLATION & PRICES",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## INFLATION & PRICES", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # CPI, PPI, Core CPI
    dashboard["panels"].append({
        "id": panel_id,
        "title": "CPI, PPI, Core CPI",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
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
                "custom": {
                    "drawStyle": "line",
                    "lineWidth": 2,
                    "fillOpacity": 10,
                    "gradientMode": "none",
                    "showPoints": "never",
                    "pointSize": 5
                },
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
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom", "calcs": []},
            "tooltip": {"mode": "single", "sort": "none"}
        }
    })
    panel_id += 1
    
    # Oil, Gas, Commodities
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Oil, Gas, Commodities",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "commodity_data")
  |> filter(fn: (r) => r.indicator == "oil_inventories" or r.indicator == "gasoline_prices" or r.indicator == "natural_gas_storage" or r.indicator == "commodity_index")
  |> keep(columns: ["_time", "_value", "indicator"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 10},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.indicator}"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "oil_inventories"}, "properties": [{"id": "displayName", "value": "Oil Inventories"}]},
                {"matcher": {"id": "byName", "options": "gasoline_prices"}, "properties": [{"id": "displayName", "value": "Gas Prices"}]},
                {"matcher": {"id": "byName", "options": "natural_gas_storage"}, "properties": [{"id": "displayName", "value": "Natural Gas"}]},
                {"matcher": {"id": "byName", "options": "commodity_index"}, "properties": [{"id": "displayName", "value": "Commodity Index"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # VIX & Credit Spreads
    dashboard["panels"].append({
        "id": panel_id,
        "title": "VIX & Credit Spreads",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => 
    (r._measurement == "market_data" and r.indicator == "vix") or
    (r._measurement == "advanced_financial" and r.indicator == "cds_spreads"))
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
                {"matcher": {"id": "byName", "options": "vix"}, "properties": [{"id": "displayName", "value": "VIX"}]},
                {"matcher": {"id": "byName", "options": "cds_spreads"}, "properties": [{"id": "displayName", "value": "Credit Spreads"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === LABOR MARKET ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "LABOR MARKET",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## LABOR MARKET", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Unemployment, NFP, Jobless Claims
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Unemployment, NFP, Jobless Claims",
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
                {"matcher": {"id": "byName", "options": "nfp"}, "properties": [{"id": "displayName", "value": "NFP (000s)"}, {"id": "custom.transform", "value": "divide-by-1000"}]},
                {"matcher": {"id": "byName", "options": "jobless_claims"}, "properties": [{"id": "displayName", "value": "Claims (000s)"}, {"id": "custom.transform", "value": "divide-by-1000"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # LFPR & Wages
    dashboard["panels"].append({
        "id": panel_id,
        "title": "LFPR & Wages",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bls_economic_data")
  |> filter(fn: (r) => r.indicator == "lfpr" or r.indicator == "wages")
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
                {"matcher": {"id": "byName", "options": "lfpr"}, "properties": [{"id": "displayName", "value": "Labor Force %"}]},
                {"matcher": {"id": "byName", "options": "wages"}, "properties": [{"id": "displayName", "value": "Wage Growth %"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Business Confidence (ISM/NFIB)
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Business Confidence (ISM/NFIB)",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "business_confidence")
  |> filter(fn: (r) => r.indicator == "ism_pmi" or r.indicator == "nfib_optimism")
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
                {"matcher": {"id": "byName", "options": "nfib_optimism"}, "properties": [{"id": "displayName", "value": "NFIB Optimism"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === GROWTH & PRODUCTION ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "GROWTH & PRODUCTION",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## GROWTH & PRODUCTION", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # GDP & Industrial Production
    dashboard["panels"].append({
        "id": panel_id,
        "title": "GDP & Industrial Production",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bea_economic_data")
  |> filter(fn: (r) => r.indicator == "gdp" or r.indicator == "industrial_production")
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
                {"matcher": {"id": "byName", "options": "gdp"}, "properties": [{"id": "displayName", "value": "GDP Growth %"}]},
                {"matcher": {"id": "byName", "options": "industrial_production"}, "properties": [{"id": "displayName", "value": "Industrial Production %"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Capacity Utilization & Global PMIs
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Capacity Utilization & Global PMIs",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => 
    (r._measurement == "bea_economic_data" and r.indicator == "capacity_utilization") or
    (r._measurement == "global_indicators" and (r.indicator == "pmi_manufacturing" or r.indicator == "pmi_services")))
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
                {"matcher": {"id": "byName", "options": "capacity_utilization"}, "properties": [{"id": "displayName", "value": "Capacity Utilization %"}]},
                {"matcher": {"id": "byName", "options": "pmi_manufacturing"}, "properties": [{"id": "displayName", "value": "Global Mfg PMI"}]},
                {"matcher": {"id": "byName", "options": "pmi_services"}, "properties": [{"id": "displayName", "value": "Global Svc PMI"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Business Inventories & Consumer Confidence
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Business Inventories & Consumer Confidence",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => 
    (r._measurement == "business_confidence" and r.indicator == "business_inventories") or
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
                {"matcher": {"id": "byName", "options": "business_inventories"}, "properties": [{"id": "displayName", "value": "Business Inventories"}]},
                {"matcher": {"id": "byName", "options": "consumer_confidence"}, "properties": [{"id": "displayName", "value": "Consumer Confidence"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === RATES & CURVES ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "RATES & CURVES",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## RATES & CURVES", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Fed Funds & SOFR
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Fed Funds & SOFR",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "fred_rates")
  |> filter(fn: (r) => r.rate_type == "fed_funds" or r.rate_type == "sofr")
  |> keep(columns: ["_time", "_value", "rate_type"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.rate_type}",
                "unit": "percent"
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "fed_funds"}, "properties": [{"id": "displayName", "value": "Fed Funds"}]},
                {"matcher": {"id": "byName", "options": "sofr"}, "properties": [{"id": "displayName", "value": "SOFR"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Treasury Yield Curve
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Treasury Yield Curve",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
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
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "${__field.labels.maturity}",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Option IV Surfaces
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Option IV Surfaces",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "advanced_financial" and r.indicator == "option_iv")
  |> keep(columns: ["_time", "_value", "term"])
''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {"drawStyle": "line", "lineWidth": 2},
                "color": {"mode": "palette-classic"},
                "displayName": "IV ${__field.labels.term}",
                "unit": "percent"
            }
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === CONSUMPTION & HOUSING ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "CONSUMPTION & HOUSING",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## CONSUMPTION & HOUSING", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Retail Sales, PCE, Durable Goods
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Retail Sales, PCE, Durable Goods",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "census_economic_data")
  |> filter(fn: (r) => r.indicator == "retail_sales" or r.indicator == "pce" or r.indicator == "durable_goods")
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
                {"matcher": {"id": "byName", "options": "retail_sales"}, "properties": [{"id": "displayName", "value": "Retail Sales"}]},
                {"matcher": {"id": "byName", "options": "pce"}, "properties": [{"id": "displayName", "value": "PCE"}]},
                {"matcher": {"id": "byName", "options": "durable_goods"}, "properties": [{"id": "displayName", "value": "Durable Goods"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Housing Starts, Building Permits, Home Sales
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Housing Starts, Building Permits, Home Sales",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "housing_data")
  |> filter(fn: (r) => r.indicator == "housing_starts" or r.indicator == "building_permits" or r.indicator == "existing_home_sales")
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
                {"matcher": {"id": "byName", "options": "building_permits"}, "properties": [{"id": "displayName", "value": "Building Permits"}]},
                {"matcher": {"id": "byName", "options": "existing_home_sales"}, "properties": [{"id": "displayName", "value": "Home Sales"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Case-Shiller Index & Mortgage Rates
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Case-Shiller Index & Mortgage Rates",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
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
    y_pos += 6
    
    # === BANKING & FINANCIAL ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "BANKING & FINANCIAL",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## BANKING & FINANCIAL", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # M1/M2 Money Supply & Bank Assets
    dashboard["panels"].append({
        "id": panel_id,
        "title": "M1/M2 Money Supply & Bank Assets",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "banking_data")
  |> filter(fn: (r) => r.indicator == "m1_money_supply" or r.indicator == "m2_money_supply" or r.indicator == "bank_assets")
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
                {"matcher": {"id": "byName", "options": "m2_money_supply"}, "properties": [{"id": "displayName", "value": "M2 Money Supply"}]},
                {"matcher": {"id": "byName", "options": "bank_assets"}, "properties": [{"id": "displayName", "value": "Bank Assets"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Corporate Profits, Bankruptcies, Margin Debt
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Corporate Profits, Bankruptcies, Margin Debt",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "corporate_data")
  |> filter(fn: (r) => r.indicator == "corporate_profits" or r.indicator == "bankruptcies" or r.indicator == "margin_debt")
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
                {"matcher": {"id": "byName", "options": "corporate_profits"}, "properties": [{"id": "displayName", "value": "Corporate Profits"}]},
                {"matcher": {"id": "byName", "options": "bankruptcies"}, "properties": [{"id": "displayName", "value": "Bankruptcies"}]},
                {"matcher": {"id": "byName", "options": "margin_debt"}, "properties": [{"id": "displayName", "value": "Margin Debt"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Equity Risk Premium & Auto Sales
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Equity Risk Premium & Auto Sales",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => 
    (r._measurement == "market_data" and r.indicator == "equity_risk_premium") or
    (r._measurement == "census_economic_data" and r.indicator == "auto_sales"))
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
                {"matcher": {"id": "byName", "options": "equity_risk_premium"}, "properties": [{"id": "displayName", "value": "Equity Risk Premium"}]},
                {"matcher": {"id": "byName", "options": "auto_sales"}, "properties": [{"id": "displayName", "value": "Auto Sales"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    y_pos += 6
    
    # === TRADE & GLOBAL ===
    dashboard["panels"].extend([
        {
            "id": panel_id,
            "title": "TRADE & GLOBAL",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {"content": "## TRADE & GLOBAL", "mode": "markdown"},
            "transparent": True
        }
    ])
    panel_id += 1
    y_pos += 2
    
    # Trade Balance, Current Account, FX Reserves
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Trade Balance, Current Account, FX Reserves",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "trade_data")
  |> filter(fn: (r) => r.indicator == "trade_balance" or r.indicator == "current_account" or r.indicator == "fx_reserves")
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
                {"matcher": {"id": "byName", "options": "current_account"}, "properties": [{"id": "displayName", "value": "Current Account"}]},
                {"matcher": {"id": "byName", "options": "fx_reserves"}, "properties": [{"id": "displayName", "value": "FX Reserves"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    # Census/Demographics
    dashboard["panels"].append({
        "id": panel_id,
        "title": "Census/Demographics",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
            "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "census_economic_data")
  |> filter(fn: (r) => r.indicator == "population_growth" or r.indicator == "household_income")
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
                {"matcher": {"id": "byName", "options": "population_growth"}, "properties": [{"id": "displayName", "value": "Population Growth"}]},
                {"matcher": {"id": "byName", "options": "household_income"}, "properties": [{"id": "displayName", "value": "Household Income"}]}
            ]
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    })
    panel_id += 1
    
    return dashboard

def main():
    print("Creating Complete Professional Dashboard")
    print("=" * 45)
    print("ALL requested indicators included:")
    print("* CPI, PPI, Core CPI, Unemployment, NFP, Jobless Claims")
    print("* LFPR, Wages, GDP, Industrial Production, Capacity Utilization")
    print("* Fed Funds, Treasuries, Yield Curve, Credit Spreads, VIX")
    print("* Retail Sales, PCE, Durable Goods, Auto Sales")
    print("* Housing Starts, Building Permits, Home Sales, Case-Shiller")
    print("* Mortgage Rates, Corporate Profits, Bankruptcies, Margin Debt")
    print("* Bank Assets, M1/M2, SOFR/Repo, Oil Inventories")
    print("* Gasoline Prices, Natural Gas Storage, Commodity Indices")
    print("* Census/Demographics, Consumer Confidence, Business Confidence")
    print("* Business Inventories, Trade Balance, Current Account, FX Reserves")
    print("* Global PMIs, Option IV surfaces, CDS spreads, Equity Risk Premium")
    
    dashboard = create_complete_dashboard()
    
    # Write dashboard file
    output_file = "grafana/provisioning/dashboards/complete_professional_dashboard.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\nDashboard created: {output_file}")
    print("\nFixed issues:")
    print("* Correct datasource UID: influxdb-datasource")
    print("* Clean legend labels using field overrides")
    print("* All requested indicators included")
    print("* Professional organization with 6 sections")
    
    print("\nNext: Restart Grafana to load the complete dashboard")

if __name__ == "__main__":
    main()