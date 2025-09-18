#!/usr/bin/env python3
"""
Create Ultra-Clean Professional Dashboard with Simple Legend Labels
Transforms verbose field names into clean, readable labels
"""

import json
from datetime import datetime

def create_ultra_clean_dashboard():
    """Create dashboard with ultra-clean legend labels"""
    
    dashboard = {
        "id": None,
        "title": "Ultra-Clean Macro Dashboard",
        "tags": ["macro", "economics", "professional", "clean"],
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
        "annotations": {
            "list": []
        },
        "templating": {
            "list": []
        }
    }
    
    panel_id = 1
    y_pos = 0
    
    # === INFLATION & LABOR SECTION ===
    panels_config = [
        {
            "title": "INFLATION & LABOR",
            "height": 6,
            "panels": [
                {
                    "title": "Core Inflation Metrics",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bls_economic_data")
  |> filter(fn: (r) => r.indicator == "cpi" or r.indicator == "core_cpi" or r.indicator == "ppi")
  |> map(fn: (r) => ({
      r with
      _value: r._value,
      _time: r._time,
      series: if r.indicator == "cpi" then "CPI"
              else if r.indicator == "core_cpi" then "Core CPI"
              else "PPI"
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Labor Market",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bls_economic_data")
  |> filter(fn: (r) => r.indicator == "unemployment_rate" or r.indicator == "nfp" or r.indicator == "lfpr")
  |> map(fn: (r) => ({
      r with
      _value: if r.indicator == "nfp" then r._value / 1000.0 else r._value,
      series: if r.indicator == "unemployment_rate" then "Unemployment"
              else if r.indicator == "nfp" then "Jobs (000s)"
              else "Labor Force %"
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Wages & Claims",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bls_economic_data")
  |> filter(fn: (r) => r.indicator == "wages" or r.indicator == "jobless_claims")
  |> map(fn: (r) => ({
      r with
      _value: if r.indicator == "jobless_claims" then r._value / 1000.0 else r._value,
      series: if r.indicator == "wages" then "Wage Growth %"
              else "Claims (000s)"
  }))
''',
                    "legend": "{{series}}"
                }
            ]
        },
        
        # === RATES & CURVES SECTION ===
        {
            "title": "RATES & CURVES",
            "height": 6,
            "panels": [
                {
                    "title": "Fed Policy & Short Rates",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "fred_rates")
  |> filter(fn: (r) => r.rate_type == "fed_funds" or r.rate_type == "sofr")
  |> map(fn: (r) => ({
      r with
      series: if r.rate_type == "fed_funds" then "Fed Funds"
              else "SOFR"
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Treasury Yield Curve",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "treasury_yield_curve")
  |> map(fn: (r) => ({
      r with
      series: if r.maturity == "3M" then "3M"
              else if r.maturity == "2Y" then "2Y"
              else if r.maturity == "10Y" then "10Y"
              else if r.maturity == "30Y" then "30Y"
              else r.maturity
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Credit & Risk",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "market_data" and r.indicator == "vix" or 
                       r._measurement == "advanced_financial" and r.indicator == "cds_spreads")
  |> map(fn: (r) => ({
      r with
      series: if r.indicator == "vix" then "VIX"
              else "CDS"
  }))
''',
                    "legend": "{{series}}"
                }
            ]
        },
        
        # === GROWTH & MARKETS SECTION ===
        {
            "title": "GROWTH & MARKETS", 
            "height": 6,
            "panels": [
                {
                    "title": "Economic Growth",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bea_economic_data")
  |> filter(fn: (r) => r.indicator == "gdp" or r.indicator == "industrial_production")
  |> map(fn: (r) => ({
      r with
      series: if r.indicator == "gdp" then "GDP Growth"
              else "Industrial Prod"
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Market Volatility",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "advanced_financial" and r.indicator == "option_iv")
  |> map(fn: (r) => ({
      r with
      series: if r.term == "30d" then "IV 30d"
              else if r.term == "60d" then "IV 60d"
              else "IV 90d"
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Global Manufacturing",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "global_indicators")
  |> filter(fn: (r) => r.indicator == "pmi_manufacturing" or r.indicator == "pmi_services")
  |> map(fn: (r) => ({
      r with
      series: if r.indicator == "pmi_manufacturing" then "Global Mfg PMI"
              else "Global Svc PMI"
  }))
''',
                    "legend": "{{series}}"
                }
            ]
        },
        
        # === CONSUMPTION & HOUSING SECTION ===
        {
            "title": "CONSUMPTION & HOUSING",
            "height": 6,
            "panels": [
                {
                    "title": "Consumer Spending",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "census_economic_data")
  |> filter(fn: (r) => r.indicator == "retail_sales" or r.indicator == "pce")
  |> map(fn: (r) => ({
      r with
      series: if r.indicator == "retail_sales" then "Retail Sales"
              else "Consumer Spending"
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Home Prices & Rates",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "housing_data")
  |> filter(fn: (r) => r.indicator == "case_shiller_index" or r.indicator == "mortgage_rates")
  |> map(fn: (r) => ({
      r with
      series: if r.indicator == "case_shiller_index" then "Home Prices"
              else "Mortgage Rates"
  }))
''',
                    "legend": "{{series}}"
                },
                {
                    "title": "Housing Activity",
                    "query": '''
from(bucket: "macro_data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "housing_data")
  |> filter(fn: (r) => r.indicator == "housing_starts" or r.indicator == "existing_home_sales")
  |> map(fn: (r) => ({
      r with
      series: if r.indicator == "housing_starts" then "Housing Starts"
              else "Home Sales"
  }))
''',
                    "legend": "{{series}}"
                }
            ]
        }
    ]
    
    # Generate panels
    for section in panels_config:
        # Add section header
        dashboard["panels"].append({
            "id": panel_id,
            "title": section["title"],
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": y_pos},
            "options": {
                "content": f"## {section['title']}",
                "mode": "markdown"
            },
            "transparent": True
        })
        panel_id += 1
        y_pos += 2
        
        # Add panels for this section
        panel_width = 24 // len(section["panels"])
        for i, panel_config in enumerate(section["panels"]):
            dashboard["panels"].append({
                "id": panel_id,
                "title": panel_config["title"],
                "type": "timeseries",
                "gridPos": {
                    "h": section["height"],
                    "w": panel_width,
                    "x": i * panel_width,
                    "y": y_pos
                },
                "targets": [{
                    "datasource": {"type": "influxdb", "uid": "influxdb-datasource"},
                    "query": panel_config["query"],
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                            "lineInterpolation": "smooth",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "displayName": panel_config["legend"],
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
                "options": {
                    "legend": {
                        "calcs": [],
                        "displayMode": "list",
                        "placement": "bottom",
                        "values": []
                    },
                    "tooltip": {"mode": "single", "sort": "none"}
                }
            })
            panel_id += 1
        
        y_pos += section["height"]
    
    return dashboard

def main():
    print("Creating Ultra-Clean Professional Dashboard")
    print("=" * 45)
    print("Simple legend labels:")
    print("* case_shiller_index -> Home Prices")
    print("* unemployment_rate -> Unemployment") 
    print("* fed_funds_rate -> Fed Funds")
    print("* nfp -> Jobs")
    print("* jobless_claims -> Claims")
    print("* And many more clean transformations...")
    
    dashboard = create_ultra_clean_dashboard()
    
    # Write dashboard file
    output_file = "grafana/provisioning/dashboards/ultra_clean_dashboard.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\nDashboard created: {output_file}")
    print("\nFeatures:")
    print("[COMPLETE] Ultra-clean legend labels")
    print("[COMPLETE] Professional organization (4 sections)")
    print("[COMPLETE] Simple, readable field names")
    print("[COMPLETE] Optimized for hedge fund/central bank use")
    
    print("\nNext: Restart Grafana to load the new dashboard")

if __name__ == "__main__":
    main()