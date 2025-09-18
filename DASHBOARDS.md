# Available Dashboards Guide

This document lists all available dashboards in your financial monitoring system.

## Dashboard Organization

Your dashboards are organized into the following folders in Grafana:

### 📊 Core Analytics
**Main financial monitoring dashboards for everyday use**

| Dashboard | Description | Key Features |
|-----------|-------------|--------------|
| `comprehensive_financial_dashboard.json` | Primary multi-asset dashboard | Stocks, crypto, forex, commodities |
| `final_comprehensive_financial_dashboard.json` | Enhanced comprehensive view | Advanced analytics integration |
| `complete_financial_dashboard_final.json` | Complete financial overview | Full market coverage |

### 🔬 Advanced Analytics
**Technical analysis and machine learning predictions**

| Dashboard | Description | Key Features |
|-----------|-------------|--------------|
| `advanced_analytics_dashboard.json` | Professional analytics suite | RSI, MACD, ML predictions |
| `advanced_visualizations_dashboard.json` | Advanced chart visualizations | Custom indicators, advanced charts |
| `combined_advanced_analytics_dashboard.json` | Combined analytics view | Integrated advanced features |

### 🌍 Economic Data
**Macro economic analysis and indicators**

| Dashboard | Description | Key Features |
|-----------|-------------|--------------|
| `macro_economic_dashboard.json` | Macro economic indicators | GDP, inflation, employment |
| `macroeconomics_dashboard_finalized.json` | Complete macro analysis | Federal Reserve data, yield curves |
| `comprehensive_macro_dashboard_combined.json` | Combined macro view | All economic indicators |

### 💼 Professional Suite
**Professional-grade analytics for advanced users**

| Dashboard | Description | Key Features |
|-----------|-------------|--------------|
| `tier2_tier3_professional_dashboard.json` | Multi-tier professional view | Extended market coverage |
| `complete_professional_dashboard.json` | Complete professional suite | All professional features |
| `complete_professional_macro_dashboard.json` | Professional macro analysis | Advanced economic modeling |

### 🎯 Specialized Views
**Custom and specialized dashboard views**

| Dashboard | Description | Key Features |
|-----------|-------------|--------------|
| `ultra_clean_dashboard.json` | Minimalist clean interface | Essential metrics only |
| `comprehensive_financial_data_analysis_fixed.json` | Data analysis focused | Deep data insights |
| `corrected_financial_dashboard.json` | Corrected version of main dashboard | Bug fixes and improvements |

## Quick Access

### Most Popular Dashboards:
1. **Comprehensive Financial Dashboard** - Best overall view
2. **Advanced Analytics Dashboard** - For technical analysis
3. **Macro Economic Dashboard** - For economic analysis

### For Different Use Cases:
- **Day Trading**: Advanced Analytics Dashboard
- **Long-term Investment**: Comprehensive Financial Dashboard
- **Economic Research**: Macro Economic Dashboard
- **Professional Analysis**: Professional Suite dashboards
- **Clean Interface**: Ultra Clean Dashboard

## Loading Dashboards

### Method 1: Automatic Reload (Recommended)
```bash
# On Linux/Mac
./reload-dashboards.sh

# On Windows
reload-dashboards.bat
```

### Method 2: Manual Docker Restart
```bash
# Stop and restart Grafana to reload dashboards
docker-compose -f docker-compose.raspberry-pi.yml restart grafana
```

### Method 3: Grafana UI Import
1. Open Grafana (http://localhost:3000)
2. Go to "+" → Import
3. Upload any `.json` file from the dashboards directory

## Dashboard Features

### 🎨 Visual Features
- **Professional color schemes** - Color-coded for different asset classes
- **Real-time updates** - 30-second refresh intervals
- **Interactive charts** - Hover for detailed information
- **Responsive design** - Works on desktop and mobile

### 📈 Data Features
- **Multi-asset coverage** - Stocks, crypto, forex, commodities
- **Technical indicators** - RSI, MACD, Bollinger Bands
- **Risk analytics** - VaR, CVaR, Sharpe ratios
- **Economic data** - Federal Reserve, BEA, EIA data

### 🔧 Customization
- **Editable panels** - Modify queries and visualizations
- **Time range selection** - From minutes to years
- **Variable templating** - Dynamic dashboard behavior
- **Export capabilities** - Save as PDF or PNG

## Troubleshooting

### Dashboards Not Appearing?
1. Check that Grafana is running: `docker ps | grep grafana`
2. Restart Grafana: `./reload-dashboards.sh`
3. Check logs: `docker-compose logs grafana`

### Missing Data?
1. Verify database connections in datasource settings
2. Check that PostgreSQL and InfluxDB are running
3. Review dashboard queries for syntax errors

### Performance Issues?
1. Reduce time range for large datasets
2. Limit concurrent dashboard refreshes
3. Consider using the "Ultra Clean" dashboard for better performance

## Dashboard Maintenance

### Regular Updates
- Dashboards auto-update every 30 seconds
- Manual refresh available in Grafana UI
- Full system restart recommended weekly

### Backup
- All dashboard files are stored in `grafana/provisioning/dashboards/`
- Backup entire directory for dashboard preservation
- Use git for version control of dashboard changes

---

**Need help?** Check the main documentation or create an issue in the repository.