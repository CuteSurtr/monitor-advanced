#!/usr/bin/env python3
"""
Create dashboard with ultra-clean legend labels
Transform verbose labels into simple, professional ones
"""

def create_clean_dashboard_json():
    """Create dashboard JSON with clean legend mappings"""
    
    dashboard = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --"
                    },
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": [
            # INFLATION & LABOR SECTION
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
                "id": 100,
                "panels": [],
                "title": "INFLATION & LABOR",
                "type": "row"
            },
            # Inflation Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 1},
                "id": 101,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "bls_economic_data")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "cpi" or r["indicator"] == "core_cpi" or r["indicator"] == "ppi")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "cpi" then "CPI"
    else if r.indicator == "core_cpi" then "Core CPI" 
    else if r.indicator == "ppi" then "PPI"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Inflation",
                "type": "timeseries"
            },
            # Unemployment Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 1},
                "id": 102,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "bls_economic_data")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "unemployment_rate" or r["indicator"] == "lfpr")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "unemployment_rate" then "Unemployment"
    else if r.indicator == "lfpr" then "Labor Force"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Labor Market",
                "type": "timeseries"
            },
            # Jobs Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "short"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 1},
                "id": 103,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "bls_economic_data")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "nfp" or r["indicator"] == "jobless_claims" or r["indicator"] == "wages")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "nfp" then "Jobs"
    else if r.indicator == "jobless_claims" then "Claims"
    else if r.indicator == "wages" then "Wages"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Jobs & Wages",
                "type": "timeseries"
            },
            
            # RATES & CURVES SECTION
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 9},
                "id": 200,
                "panels": [],
                "title": "RATES & CURVES",
                "type": "row"
            },
            # Fed Funds Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 10},
                "id": 201,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fred_economic_data")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "fed_funds_rate")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: "Fed Funds" }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Fed Funds Rate",
                "type": "timeseries"
            },
            # Treasury Yields Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 10},
                "id": 202,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "treasury_yield_curve")
  |> filter(fn: (r) => r["_field"] == "yield")
  |> filter(fn: (r) => r["maturity"] == "2Y" or r["maturity"] == "10Y" or r["maturity"] == "30Y")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.maturity }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Treasury Yields",
                "type": "timeseries"
            },
            # Yield Spread Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 10},
                "id": 203,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "treasury_curve_metrics")
  |> filter(fn: (r) => r["_field"] == "spread")
  |> filter(fn: (r) => r["metric"] == "10y_2y_spread")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: "10Y-2Y" }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Yield Spread",
                "type": "timeseries"
            },
            
            # GROWTH & MARKETS SECTION
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 18},
                "id": 300,
                "panels": [],
                "title": "GROWTH & MARKETS",
                "type": "row"
            },
            # GDP Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 19},
                "id": 301,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "bea_economic_data")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "gdp_growth" or r["indicator"] == "industrial_production")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "gdp_growth" then "GDP"
    else if r.indicator == "industrial_production" then "Industrial"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Growth",
                "type": "timeseries"
            },
            # VIX Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "short"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 19},
                "id": 302,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fred_economic_data")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "vix")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: "VIX" }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Volatility (VIX)",
                "type": "timeseries"
            },
            # Credit Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "short"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 19},
                "id": 303,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "advanced_financial")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "credit_spread" or r["indicator"] == "cds_spreads")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "credit_spread" and r.grade == "investment_grade" then "IG"
    else if r.indicator == "credit_spread" and r.grade == "high_yield" then "HY" 
    else if r.indicator == "cds_spreads" then "CDS"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Credit Spreads",
                "type": "timeseries"
            },
            
            # CONSUMPTION & HOUSING SECTION
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 27},
                "id": 400,
                "panels": [],
                "title": "CONSUMPTION & HOUSING",
                "type": "row"
            },
            # Retail Sales Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 28},
                "id": 401,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "trade_consumption")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "retail_sales" or r["indicator"] == "pce")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "retail_sales" and r.type == "headline" then "Retail Sales"
    else if r.indicator == "retail_sales" and r.type == "core" then "Retail Core"
    else if r.indicator == "pce" and r.type == "headline" then "PCE"
    else if r.indicator == "pce" and r.type == "core" then "PCE Core"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Consumer Spending",
                "type": "timeseries"
            },
            # Housing Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "short"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 28},
                "id": 402,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "housing_real_estate")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "housing_starts" or r["indicator"] == "new_home_sales")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "housing_starts" then "Starts"
    else if r.indicator == "new_home_sales" then "Sales"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Housing Activity",
                "type": "timeseries"
            },
            # Case Shiller Panel
            {
                "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisBorderShow": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": "short"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 28},
                "id": 403,
                "options": {
                    "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                        "query": """from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "housing_real_estate")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["indicator"] == "case_shiller_index" or r["indicator"] == "mortgage_30y")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: 
    if r.indicator == "case_shiller_index" then "Home Prices"
    else if r.indicator == "mortgage_30y" then "Mortgage Rate"
    else r.indicator
  }))
  |> yield(name: "mean")""",
                        "refId": "A"
                    }
                ],
                "title": "Housing Prices",
                "type": "timeseries"
            }
        ],
        "refresh": "",
        "schemaVersion": 39,
        "tags": ["macro", "clean", "professional"],
        "templating": {"list": []},
        "time": {"from": "now-6M", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": "Clean Macro Dashboard",
        "uid": "clean_macro_dashboard",
        "version": 1,
        "weekStart": ""
    }
    
    return dashboard

def main():
    import json
    
    dashboard = create_clean_dashboard_json()
    
    with open('C:/Users/nex88/OneDrive/Desktop/monitor advanced/grafana/provisioning/dashboards/clean_macro_dashboard.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print("Created ultra-clean dashboard with simplified legend labels:")
    print("• Inflation: CPI, Core CPI, PPI")
    print("• Labor Market: Unemployment, Labor Force")
    print("• Jobs & Wages: Jobs, Claims, Wages")
    print("• Fed Funds: Fed Funds")
    print("• Treasury Yields: 2Y, 10Y, 30Y")
    print("• Yield Spread: 10Y-2Y")
    print("• Growth: GDP, Industrial")
    print("• Volatility: VIX")
    print("• Credit Spreads: IG, HY, CDS")
    print("• Consumer Spending: Retail Sales, Retail Core, PCE, PCE Core")
    print("• Housing Activity: Starts, Sales")
    print("• Housing Prices: Home Prices, Mortgage Rate")

if __name__ == "__main__":
    main()