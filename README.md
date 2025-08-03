# 24/7 Global Stock Market Monitoring System

A comprehensive real-time stock market monitoring system designed for Raspberry Pi with advanced analytics, portfolio management, and Prometheus integration.

## Features

### Core Monitoring
- **Real-time multi-exchange data collection** (US, European, Asian exchanges)
- **Commodities price tracking** (gold, silver, oil, copper, agricultural products)
- **Automatic market switching by timezone** (24-hour global market tracking)
- **Real-time alert system** for watchlist stocks and sudden price movements

### Advanced Analytics
- **Technical indicators** (RSI, MACD, Bollinger Bands, moving averages)
- **Sector/regional performance comparison**
- **Correlation analysis** (stocks, commodities, currencies)
- **Volatility analysis and risk measurement**
- **ML-based anomaly detection**
- **Economic calendar integration**

### Portfolio Management
- **Real portfolio tracking** (buy/sell records)
- **P&L calculation and performance analysis**
- **Rebalancing suggestions**
- **Tax optimization calculations**

### Monitoring & Visualization
- **Web-based interactive dashboard** (charts, heatmaps, portfolio)
- **Prometheus metrics collection**
- **Grafana dashboards**
- **News crawling and sentiment analysis**

## Project Structure

```
monitor-advanced/
├── config/                 # Configuration files
├── data/                   # Data storage
├── src/                    # Source code
│   ├── collectors/         # Data collection modules
│   ├── analytics/          # Analytics and ML modules
│   ├── portfolio/          # Portfolio management
│   ├── alerts/             # Alert system
│   ├── dashboard/          # Web dashboard
│   ├── monitoring/         # Prometheus integration
│   └── utils/              # Utility functions
├── tests/                  # Test files
├── docs/                   # Documentation
├── docker/                 # Docker configurations
├── prometheus/             # Prometheus configs
├── grafana/                # Grafana dashboards
└── scripts/                # Setup and maintenance scripts
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp config/config.example.yaml config/config.yaml
   # Edit config.yaml with your API keys and settings
   ```

3. **Initialize database:**
   ```bash
   python scripts/init_db.py
   ```

4. **Start the system:**
   ```bash
   python src/main.py
   ```

5. **Access dashboard:**
   - Web Dashboard: http://localhost:8080
   - Grafana: http://localhost:3000
   - Prometheus: http://localhost:9090

## Requirements

- Raspberry Pi 4 (4GB+ RAM recommended)
- Python 3.8+
- PostgreSQL/InfluxDB
- Docker (optional)
- Internet connection for real-time data

## Performance Optimization

- Optimized for Raspberry Pi ARM architecture
- Efficient memory usage with data streaming
- Background processing for heavy computations
- Caching strategies for API calls
- Database indexing for fast queries

## License

MIT License 